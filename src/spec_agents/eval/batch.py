"""Anthropic Batch-API wrapper for the eval harness (XR-011).

Library mode: thin wrappers around the SDK's batch endpoints. The kernel
provides submit / status / fetch / wait / invoker-builder; the caller
builds the per-run request dicts (with whatever prompt + lens + model
choices they need).

Why batches: the Batch API is 50 percent cheaper and turns over within
~24 hours. For eval-rig replays of 100s of historical runs (XR-010 +
SR-007 / SR-008 / LENS-001), live calls cost real money; batches cost
half and don't block.

Typical flow:

    from spec_agents.eval import run_eval
    from spec_agents.eval.batch import (
        submit_batch, wait_for_batch, fetch_results, build_invoker,
    )

    # 1. Build per-run params (prompt + lens + model).
    requests = [
        {"custom_id": str(run.run_id), "params": build_anthropic_params(run)}
        for run in runs
    ]

    # 2. Submit + wait.
    batch_id = submit_batch(client=client, requests=requests)
    wait_for_batch(client=client, batch_id=batch_id)
    results = fetch_results(client=client, batch_id=batch_id)

    # 3. Score via the normal eval-harness loop.
    invoker = build_invoker(results)
    eval_results = run_eval(runs=runs, invoker=invoker, scorer=my_scorer)

Per the v2 charter: this wraps SA-002 / XR-010 / SA-003 without changing
their contracts. Apps that use this code stay vendor-neutral on content;
the Anthropic-specific bit is contained to ``submit_batch``,
``get_batch_status``, ``fetch_results``, and ``wait_for_batch``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import anthropic
import structlog

from spec_agents.eval.runner import EvalRun, Invoker

log = structlog.get_logger()


@dataclass(frozen=True)
class BatchResult:
    """One batched call's outcome.

    ``custom_id`` matches the ``custom_id`` the caller submitted (the
    convention is to use the eval ``run_id`` so ``build_invoker`` can
    map back). ``response`` is the parsed message body on success;
    ``error`` carries a short error string on failure (the kernel
    doesn't try to interpret the SDK's error union — caller's choice).
    """

    custom_id: str
    response: dict[str, Any] | None
    error: str | None = None


def submit_batch(
    *,
    client: anthropic.Anthropic,
    requests: list[dict[str, Any]],
) -> str:
    """Submit a batch of message-create calls.

    Args:
        client: Pre-constructed Anthropic client.
        requests: List of ``{"custom_id": ..., "params": {...}}`` dicts.
            Each ``params`` dict is what you'd pass to
            ``client.messages.create(**params)``.

    Returns the batch_id, which the rest of this module uses to track
    the batch.
    """
    batch = client.messages.batches.create(requests=requests)  # pyright: ignore[reportArgumentType]
    batch_id: str = batch.id  # pyright: ignore[reportAttributeAccessIssue]
    log.info("batch.submitted", batch_id=batch_id, n_requests=len(requests))
    return batch_id


def get_batch_status(*, client: anthropic.Anthropic, batch_id: str) -> str:
    """Return the batch's current ``processing_status``.

    Anthropic publishes a small enum: typically ``in_progress``,
    ``canceling``, or ``ended``. Treat anything other than ``in_progress``
    as terminal.
    """
    batch = client.messages.batches.retrieve(batch_id)
    status: str = batch.processing_status  # pyright: ignore[reportAttributeAccessIssue]
    return status


def wait_for_batch(
    *,
    client: anthropic.Anthropic,
    batch_id: str,
    poll_interval: float = 60.0,
    timeout: float | None = None,
    sleep: Any = time.sleep,
) -> str:
    """Block until the batch reaches a terminal status.

    Args:
        client: Pre-constructed Anthropic client.
        batch_id: ID from ``submit_batch``.
        poll_interval: Seconds between status checks. Default 60 — the
            Batch API SLA is on the order of hours, so polling more
            often just wastes calls.
        timeout: Max seconds to wait. ``None`` means wait forever.
        sleep: Injection point for tests. Default ``time.sleep``.

    Returns the final ``processing_status``. Raises ``TimeoutError`` if
    the batch is still ``in_progress`` past the timeout.
    """
    start = time.monotonic()
    while True:
        status = get_batch_status(client=client, batch_id=batch_id)
        if status != "in_progress":
            log.info(
                "batch.terminal",
                batch_id=batch_id,
                status=status,
                elapsed_seconds=round(time.monotonic() - start, 1),
            )
            return status
        if timeout is not None and time.monotonic() - start > timeout:
            raise TimeoutError(f"Batch {batch_id} still in_progress after {timeout}s")
        sleep(poll_interval)


def fetch_results(
    *,
    client: anthropic.Anthropic,
    batch_id: str,
) -> list[BatchResult]:
    """Fetch all per-request results from a completed batch.

    The SDK returns an iterator of
    ``MessageBatchIndividualResponse`` objects; this function flattens
    each to a ``BatchResult``, success or failure. Order is the SDK's
    (typically the order the batch returns them, not submission order).
    """
    out: list[BatchResult] = []
    for raw in client.messages.batches.results(batch_id):
        item: Any = raw
        custom_id: str = item.custom_id
        result_type: str = getattr(item.result, "type", "unknown")
        if result_type == "succeeded":
            try:
                response = item.result.message.model_dump()
            except Exception as exc:  # pragma: no cover (SDK shape guard)
                out.append(
                    BatchResult(
                        custom_id=custom_id,
                        response=None,
                        error=f"could not parse succeeded response: {exc}",
                    )
                )
                continue
            out.append(BatchResult(custom_id=custom_id, response=response))
        else:
            out.append(
                BatchResult(
                    custom_id=custom_id,
                    response=None,
                    error=f"{result_type}: {item.result!r}",
                )
            )
    log.info("batch.results_fetched", batch_id=batch_id, n=len(out))
    return out


def build_invoker(results: list[BatchResult]) -> Invoker:
    """Build an eval ``Invoker`` that looks up by ``run_id`` (= custom_id).

    Use this after ``fetch_results`` to feed the batched outputs through
    ``run_eval`` exactly like a live invoker — same Scorer code, same
    aggregation. Runs missing from the results raise ``KeyError`` (so
    the eval-harness skip-on-invoke-error logic can decide whether to
    swallow or surface).
    """
    by_id: dict[str, BatchResult] = {r.custom_id: r for r in results}

    def invoke(run: EvalRun) -> dict[str, Any]:
        r = by_id.get(run.run_id)
        if r is None:
            raise KeyError(f"no batch result for run_id={run.run_id!r}")
        if r.error or r.response is None:
            raise RuntimeError(f"batch error for {run.run_id!r}: {r.error}")
        return r.response

    return invoke
