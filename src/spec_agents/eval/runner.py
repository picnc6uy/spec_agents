"""Eval-harness runner (library-mode, XR-010).

The kernel provides the loop + simple aggregation. The caller owns
everything domain-specific:

- ``Invoker``: takes an ``EvalRun`` and returns the model's actual output
  (whatever shape the consumer wants). The invoker holds prompt assembly,
  lens loading, API call, and result parsing.
- ``Scorer``: takes the run + the actual output and returns a score
  (float, dict, bool — whatever the domain measures). The scorer holds
  the ground truth comparison.

Typical consumer flow:

    from spec_agents.eval import run_eval, aggregate_numeric, EvalRun

    runs = [EvalRun(run_id=row.id, inputs={...}, expected=row.outcome)
            for row in session.execute(select(Brief)).scalars()]

    def invoke_brief(run: EvalRun) -> dict:
        # build prompt, call Anthropic, return parsed dict
        ...

    def brier(run: EvalRun, actual: dict) -> float:
        # (actual_prob - actual_outcome) ** 2
        ...

    results = run_eval(runs=runs, invoker=invoke_brief, scorer=brier)
    stats = aggregate_numeric(results)  # mean / std / count
"""

from __future__ import annotations

import statistics
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

import structlog

log = structlog.get_logger()


@dataclass(frozen=True)
class EvalRun:
    """One historical run to replay + score.

    Domain-agnostic. ``inputs`` is whatever the consumer's invoker needs
    (prompts, signal rows, lens names, prompt_version, etc.). ``expected``
    is whatever the consumer's scorer compares against (a label, target
    probability, expected schema, etc.).
    """

    run_id: str
    inputs: dict[str, Any] = field(default_factory=dict)
    expected: Any = None


@dataclass(frozen=True)
class EvalResult:
    """One replay's outcome. ``score`` carries whatever the scorer returns."""

    run_id: str
    actual: dict[str, Any]
    score: Any


# Type aliases — protocols would be slightly stricter but plain callables
# compose more naturally for ad-hoc scorers / invokers.
Invoker = Callable[[EvalRun], dict[str, Any]]
Scorer = Callable[[EvalRun, dict[str, Any]], Any]


def run_eval(
    *,
    runs: Sequence[EvalRun],
    invoker: Invoker,
    scorer: Scorer,
    skip_on_invoke_error: bool = True,
    skip_on_scorer_error: bool = True,
) -> list[EvalResult]:
    """Iterate runs, invoke, score, return results.

    Args:
        runs: Historical runs to replay.
        invoker: Given an ``EvalRun``, returns the model's actual output
            as a dict. For Batch usage (XR-011), this would look up
            previously-batched results by ``run_id`` rather than calling
            the model live.
        scorer: Given ``(run, actual)``, returns a score (any shape).
        skip_on_invoke_error: When True (default), invoker exceptions are
            logged and the run is skipped. When False, exceptions propagate
            — useful in tests that want to assert on failures.
        skip_on_scorer_error: Same shape for scorer exceptions.

    Returns:
        ``list[EvalResult]`` for runs that completed both invoke and
        score. Skipped runs are absent from the output (use
        ``len(runs) - len(results)`` to count drops).

    Library mode: no state held; no shared resources; sequential. XR-011
    (Batch API) wraps this without changing the contract.
    """
    results: list[EvalResult] = []
    for run in runs:
        try:
            actual = invoker(run)
        except Exception as exc:
            if not skip_on_invoke_error:
                raise
            log.warning("eval.invoke_failed", run_id=run.run_id, error=str(exc))
            continue
        try:
            score = scorer(run, actual)
        except Exception as exc:
            if not skip_on_scorer_error:
                raise
            log.warning("eval.score_failed", run_id=run.run_id, error=str(exc))
            continue
        results.append(EvalResult(run_id=run.run_id, actual=actual, score=score))
    return results


def aggregate_numeric(results: Sequence[EvalResult]) -> dict[str, float]:
    """Mean / std / count when scores are numeric (Brier-style).

    Non-numeric scores in the input are silently ignored. For
    dict-shaped scores (per-criterion), compose this per-key in the
    consumer rather than expanding the kernel's surface.

    Returns a dict with keys ``count``, ``mean``, ``std``. Empty / no
    numeric results returns ``count=0`` and NaN for the rest.
    """
    scores: list[float] = [float(r.score) for r in results if isinstance(r.score, int | float)]
    if not scores:
        return {"count": 0.0, "mean": float("nan"), "std": float("nan")}
    if len(scores) == 1:
        return {"count": 1.0, "mean": float(scores[0]), "std": 0.0}
    return {
        "count": float(len(scores)),
        "mean": statistics.mean(scores),
        "std": statistics.stdev(scores),
    }
