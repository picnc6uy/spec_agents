"""Smoke tests for spec_agents.eval (XR-010)."""

from __future__ import annotations

import math
from typing import Any

import pytest

from spec_agents.eval import EvalResult, EvalRun, aggregate_numeric, run_eval


def _echo_invoker(run: EvalRun) -> dict[str, Any]:
    """Trivial invoker: returns the run's `inputs` plus a synthetic field."""
    return {**run.inputs, "_replayed": True}


def _equality_scorer(run: EvalRun, actual: dict[str, Any]) -> float:
    """Score = 1.0 if actual["x"] == expected else 0.0."""
    return 1.0 if actual.get("x") == run.expected else 0.0


def test_run_eval_round_trips() -> None:
    runs = [
        EvalRun(run_id="r1", inputs={"x": 1}, expected=1),
        EvalRun(run_id="r2", inputs={"x": 2}, expected=99),
    ]
    results = run_eval(runs=runs, invoker=_echo_invoker, scorer=_equality_scorer)

    assert len(results) == 2
    assert results[0].run_id == "r1"
    assert results[0].score == 1.0  # matched
    assert results[1].run_id == "r2"
    assert results[1].score == 0.0  # mismatched
    assert results[0].actual == {"x": 1, "_replayed": True}


def test_run_eval_empty_runs() -> None:
    results = run_eval(runs=[], invoker=_echo_invoker, scorer=_equality_scorer)
    assert results == []


def test_run_eval_skips_on_invoke_error_by_default() -> None:
    def broken_invoker(run: EvalRun) -> dict[str, Any]:
        if run.run_id == "bad":
            raise RuntimeError("simulated invoker failure")
        return _echo_invoker(run)

    runs = [
        EvalRun(run_id="ok", inputs={"x": 1}, expected=1),
        EvalRun(run_id="bad", inputs={"x": 2}, expected=2),
        EvalRun(run_id="ok2", inputs={"x": 3}, expected=3),
    ]
    results = run_eval(runs=runs, invoker=broken_invoker, scorer=_equality_scorer)
    assert [r.run_id for r in results] == ["ok", "ok2"]


def test_run_eval_propagates_invoke_error_when_skip_false() -> None:
    def broken_invoker(_run: EvalRun) -> dict[str, Any]:
        raise RuntimeError("nope")

    with pytest.raises(RuntimeError, match="nope"):
        run_eval(
            runs=[EvalRun(run_id="r1")],
            invoker=broken_invoker,
            scorer=_equality_scorer,
            skip_on_invoke_error=False,
        )


def test_run_eval_skips_on_scorer_error_by_default() -> None:
    def broken_scorer(run: EvalRun, _actual: dict[str, Any]) -> float:
        if run.run_id == "bad":
            raise ValueError("scorer crash")
        return 0.5

    runs = [
        EvalRun(run_id="ok"),
        EvalRun(run_id="bad"),
        EvalRun(run_id="ok2"),
    ]
    results = run_eval(runs=runs, invoker=_echo_invoker, scorer=broken_scorer)
    assert [r.run_id for r in results] == ["ok", "ok2"]


def test_run_eval_propagates_scorer_error_when_skip_false() -> None:
    def crashy_scorer(_run: EvalRun, _actual: dict[str, Any]) -> float:
        raise ValueError("nope")

    with pytest.raises(ValueError, match="nope"):
        run_eval(
            runs=[EvalRun(run_id="r1")],
            invoker=_echo_invoker,
            scorer=crashy_scorer,
            skip_on_scorer_error=False,
        )


def test_aggregate_numeric_empty() -> None:
    stats = aggregate_numeric([])
    assert stats["count"] == 0
    assert math.isnan(stats["mean"])
    assert math.isnan(stats["std"])


def test_aggregate_numeric_single_run() -> None:
    results = [EvalResult(run_id="r1", actual={}, score=0.42)]
    stats = aggregate_numeric(results)
    assert stats == {"count": 1.0, "mean": 0.42, "std": 0.0}


def test_aggregate_numeric_multiple_runs() -> None:
    results = [
        EvalResult(run_id="r1", actual={}, score=0.2),
        EvalResult(run_id="r2", actual={}, score=0.4),
        EvalResult(run_id="r3", actual={}, score=0.6),
    ]
    stats = aggregate_numeric(results)
    assert stats["count"] == 3
    assert stats["mean"] == pytest.approx(0.4)
    assert stats["std"] == pytest.approx(0.2)


def test_aggregate_numeric_ignores_non_numeric_scores() -> None:
    """A consumer using dict-shaped scores might still call aggregate_numeric
    by mistake — kernel filters silently rather than raising."""
    results = [
        EvalResult(run_id="r1", actual={}, score=0.5),
        EvalResult(run_id="r2", actual={}, score={"criterion_a": 0.7}),  # dict — ignored
        EvalResult(run_id="r3", actual={}, score=True),  # bool happens to be numeric in Python
        EvalResult(run_id="r4", actual={}, score="bad"),  # str — ignored
    ]
    stats = aggregate_numeric(results)
    # 0.5 and True (== 1.0) survive the isinstance(int|float) filter
    assert stats["count"] == 2
    assert stats["mean"] == pytest.approx(0.75)
