"""Smoke tests for spec_agents.eval.batch (XR-011).

Uses stub Anthropic clients. Live-batch behavior is exercised by
consumers (SR-007 / SR-008 / LENS-001 once those land).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from spec_agents.eval import EvalRun
from spec_agents.eval.batch import (
    BatchResult,
    build_invoker,
    fetch_results,
    get_batch_status,
    submit_batch,
    wait_for_batch,
)

# ── Stub Anthropic client mimicking the slice of the SDK we touch ─────


@dataclass
class _StubBatch:
    id: str
    processing_status: str


@dataclass
class _StubMessage:
    """Mimics MessageBatchIndividualResponse.result.message."""

    payload: dict[str, Any]

    def model_dump(self) -> dict[str, Any]:
        return dict(self.payload)


@dataclass
class _StubResult:
    """Mimics MessageBatchIndividualResponse.result."""

    type: str
    message: _StubMessage | None = None


@dataclass
class _StubResponseItem:
    """Mimics MessageBatchIndividualResponse itself."""

    custom_id: str
    result: _StubResult


@dataclass
class _StubBatchesAPI:
    """Mimics client.messages.batches."""

    submitted: list[dict[str, Any]] = field(default_factory=list)
    status_sequence: list[str] = field(default_factory=lambda: ["ended"])
    results_iter: list[_StubResponseItem] = field(default_factory=list)
    next_status_index: int = 0

    def create(self, *, requests: list[dict[str, Any]]) -> _StubBatch:
        self.submitted = list(requests)
        return _StubBatch(id="batch_test", processing_status="in_progress")

    def retrieve(self, batch_id: str) -> _StubBatch:
        # Pop next status, sticking on the last entry.
        idx = min(self.next_status_index, len(self.status_sequence) - 1)
        status = self.status_sequence[idx]
        self.next_status_index += 1
        return _StubBatch(id=batch_id, processing_status=status)

    def results(self, batch_id: str) -> list[_StubResponseItem]:
        return list(self.results_iter)


@dataclass
class _StubMessagesAPI:
    batches: _StubBatchesAPI = field(default_factory=_StubBatchesAPI)


@dataclass
class _StubClient:
    messages: _StubMessagesAPI = field(default_factory=_StubMessagesAPI)


# ── Tests ────────────────────────────────────────────────────────────


def test_submit_batch_returns_id_and_forwards_requests() -> None:
    client = _StubClient()
    reqs = [
        {"custom_id": "r1", "params": {"model": "claude-sonnet-4-6"}},
        {"custom_id": "r2", "params": {"model": "claude-sonnet-4-6"}},
    ]
    batch_id = submit_batch(client=client, requests=reqs)  # type: ignore[arg-type]
    assert batch_id == "batch_test"
    assert client.messages.batches.submitted == reqs


def test_get_batch_status_passes_through() -> None:
    client = _StubClient()
    client.messages.batches.status_sequence = ["in_progress"]
    status = get_batch_status(client=client, batch_id="b1")  # type: ignore[arg-type]
    assert status == "in_progress"


def test_wait_for_batch_polls_until_terminal() -> None:
    client = _StubClient()
    client.messages.batches.status_sequence = ["in_progress", "in_progress", "ended"]
    sleeps: list[float] = []

    def fake_sleep(s: float) -> None:
        sleeps.append(s)

    final = wait_for_batch(
        client=client,  # type: ignore[arg-type]
        batch_id="b1",
        poll_interval=0.1,
        sleep=fake_sleep,
    )
    assert final == "ended"
    # Slept twice (after the two in_progress responses).
    assert sleeps == [0.1, 0.1]


def test_wait_for_batch_returns_immediately_on_terminal() -> None:
    client = _StubClient()
    client.messages.batches.status_sequence = ["ended"]
    sleeps: list[float] = []

    final = wait_for_batch(
        client=client,  # type: ignore[arg-type]
        batch_id="b1",
        poll_interval=0.1,
        sleep=sleeps.append,
    )
    assert final == "ended"
    assert sleeps == []  # never slept


def test_wait_for_batch_times_out() -> None:
    """Stuck-in-progress raises TimeoutError once `timeout` elapses."""
    client = _StubClient()
    client.messages.batches.status_sequence = ["in_progress"]  # sticks

    # We pin time.monotonic via a counter to simulate elapsed time.
    import spec_agents.eval.batch as batch_mod

    times = iter([0.0, 0.5, 1.0, 1.5, 2.0])

    def fake_monotonic() -> float:
        return next(times)

    sleeps: list[float] = []

    original_monotonic = batch_mod.time.monotonic
    batch_mod.time.monotonic = fake_monotonic  # type: ignore[assignment]
    try:
        with pytest.raises(TimeoutError, match="still in_progress after 1"):
            wait_for_batch(
                client=client,  # type: ignore[arg-type]
                batch_id="b1",
                poll_interval=0.1,
                timeout=1.0,
                sleep=sleeps.append,
            )
    finally:
        batch_mod.time.monotonic = original_monotonic  # type: ignore[assignment]


def test_fetch_results_splits_success_and_error_items() -> None:
    client = _StubClient()
    client.messages.batches.results_iter = [
        _StubResponseItem(
            custom_id="r1",
            result=_StubResult(type="succeeded", message=_StubMessage({"verdict": "approved"})),
        ),
        _StubResponseItem(
            custom_id="r2",
            result=_StubResult(type="errored"),  # SDK enum-style failure
        ),
    ]
    results = fetch_results(client=client, batch_id="b1")  # type: ignore[arg-type]
    assert len(results) == 2
    by_id = {r.custom_id: r for r in results}
    assert by_id["r1"].response == {"verdict": "approved"}
    assert by_id["r1"].error is None
    assert by_id["r2"].response is None
    assert "errored" in (by_id["r2"].error or "")


def test_build_invoker_round_trips_through_run_eval() -> None:
    """Integration: a stub batch result feeds run_eval via the built invoker."""
    from spec_agents.eval import run_eval

    runs = [
        EvalRun(run_id="r1", inputs={"prompt": "hi"}, expected=1),
        EvalRun(run_id="r2", inputs={"prompt": "ho"}, expected=2),
    ]
    batched = [
        BatchResult(custom_id="r1", response={"verdict": "approved", "score": 1}),
        BatchResult(custom_id="r2", response={"verdict": "rejected", "score": 0}),
    ]

    def trivial_scorer(run: EvalRun, actual: dict[str, Any]) -> float:
        return 1.0 if actual["score"] == run.expected else 0.0

    invoker = build_invoker(batched)
    results = run_eval(runs=runs, invoker=invoker, scorer=trivial_scorer)
    assert len(results) == 2
    assert results[0].run_id == "r1" and results[0].score == 1.0
    assert results[1].run_id == "r2" and results[1].score == 0.0


def test_build_invoker_raises_keyerror_for_missing_run() -> None:
    invoker = build_invoker([BatchResult(custom_id="r1", response={"x": 1})])
    with pytest.raises(KeyError, match="r_missing"):
        invoker(EvalRun(run_id="r_missing"))


def test_build_invoker_raises_runtimeerror_for_errored_result() -> None:
    invoker = build_invoker([BatchResult(custom_id="r1", response=None, error="rate_limited")])
    with pytest.raises(RuntimeError, match="rate_limited"):
        invoker(EvalRun(run_id="r1"))


def test_build_invoker_missing_results_play_well_with_run_eval_skip() -> None:
    """End-to-end: when batched results don't cover all runs, run_eval's
    default skip behavior keeps the rest moving."""
    from spec_agents.eval import run_eval

    runs = [
        EvalRun(run_id="r1", expected=1),
        EvalRun(run_id="r2_missing", expected=2),
        EvalRun(run_id="r3", expected=3),
    ]
    batched = [
        BatchResult(custom_id="r1", response={"v": 1}),
        BatchResult(custom_id="r3", response={"v": 3}),
        # r2_missing absent
    ]

    invoker = build_invoker(batched)

    def scorer(run: EvalRun, actual: dict[str, Any]) -> float:
        return 1.0 if actual["v"] == run.expected else 0.0

    results = run_eval(runs=runs, invoker=invoker, scorer=scorer)
    # r1 and r3 succeed; r2_missing's KeyError gets swallowed by default.
    assert [r.run_id for r in results] == ["r1", "r3"]
