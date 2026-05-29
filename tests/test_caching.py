"""Tests for spec_agents.caching (token-wise prompt-cache helpers)."""

from __future__ import annotations

import threading

import pytest

from spec_agents.caching import (
    cached_text_block,
    is_cache_churning,
    warm_then_fan_out,
)

# ── cached_text_block ───────────────────────────────────────────────────


def test_cached_text_block_shape() -> None:
    block = cached_text_block("corpus text")
    assert block == {
        "type": "text",
        "text": "corpus text",
        "cache_control": {"type": "ephemeral"},
    }


def test_cached_text_block_returns_fresh_cache_control_each_call() -> None:
    # No shared-mutable aliasing: mutating one block's cache_control must not
    # leak into the next.
    a = cached_text_block("a")
    b = cached_text_block("b")
    assert a["cache_control"] is not b["cache_control"]
    a["cache_control"]["type"] = "mutated"
    assert b["cache_control"] == {"type": "ephemeral"}


# ── warm_then_fan_out: basics ───────────────────────────────────────────


def test_warm_then_fan_out_empty_returns_empty() -> None:
    assert warm_then_fan_out([], lambda t: t) == []


def test_warm_then_fan_out_single_task() -> None:
    assert warm_then_fan_out(["only"], lambda t: t.upper()) == ["ONLY"]


def test_warm_then_fan_out_preserves_input_order() -> None:
    # Even though fan-out completes out of order, results match input order.
    tasks = list(range(10))
    result = warm_then_fan_out(tasks, lambda t: t * t, max_workers=4)
    assert result == [t * t for t in tasks]


def test_warm_then_fan_out_runs_every_task_once() -> None:
    seen: list[int] = []
    lock = threading.Lock()

    def run(t: int) -> int:
        with lock:
            seen.append(t)
        return t

    warm_then_fan_out([1, 2, 3, 4, 5], run)
    assert sorted(seen) == [1, 2, 3, 4, 5]
    assert len(seen) == 5  # no duplicates / retries


# ── warm_then_fan_out: the warm-before-fan-out guarantee ────────────────


def test_warm_true_completes_first_task_before_any_fanout_starts() -> None:
    """The core guarantee: with warm=True, tasks[0] finishes (cache created)
    before any other task starts (so the rest cache-READ, not re-create)."""
    warmed = threading.Event()
    violations: list[str] = []

    def run(task: str) -> str:
        if task == "warm":
            warmed.set()
        else:
            if not warmed.is_set():
                violations.append(task)  # started before warm-up landed
        return task

    tasks = ["warm", "f1", "f2", "f3", "f4", "f5"]
    result = warm_then_fan_out(tasks, run, warm=True, max_workers=5)
    assert result == tasks  # order preserved
    assert violations == [], f"fan-out tasks started before warm-up: {violations}"


def test_warm_false_does_not_serialize_a_warmup() -> None:
    # warm=False fans everything out; still runs all tasks and preserves order.
    tasks = ["a", "b", "c", "d"]
    result = warm_then_fan_out(tasks, lambda t: t * 2, warm=False)
    assert result == ["aa", "bb", "cc", "dd"]


def test_warm_then_fan_out_propagates_exceptions() -> None:
    def run(t: int) -> int:
        if t == 3:
            raise ValueError("boom on 3")
        return t

    with pytest.raises(ValueError, match="boom on 3"):
        warm_then_fan_out([1, 2, 3, 4], run)


def test_warm_then_fan_out_warmup_exception_propagates_before_fanout() -> None:
    ran_fanout = threading.Event()

    def run(t: int) -> int:
        if t == 0:
            raise RuntimeError("warmup failed")
        ran_fanout.set()
        return t

    with pytest.raises(RuntimeError, match="warmup failed"):
        warm_then_fan_out([0, 1, 2], run, warm=True)
    assert not ran_fanout.is_set(), "fan-out ran despite warm-up failure"


# ── is_cache_churning ───────────────────────────────────────────────────


def test_churn_false_when_no_creation() -> None:
    assert is_cache_churning(0, 1_000_000) is False


def test_churn_true_when_creation_and_zero_reads() -> None:
    assert is_cache_churning(130_000, 0) is True


def test_churn_true_when_creation_dwarfs_reads() -> None:
    # The audit-DAG signature: lots of creation, fewer reads.
    assert is_cache_churning(551_000, 110_000) is True


def test_churn_false_for_healthy_cache() -> None:
    # Warm-then-fan-out ideal: write once, read many.
    assert is_cache_churning(130_000, 1_100_000) is False


def test_churn_threshold_is_configurable() -> None:
    # 0.5 ratio: not churning at the default 1.0 threshold, but is at 0.4.
    assert is_cache_churning(50, 100, threshold=1.0) is False
    assert is_cache_churning(50, 100, threshold=0.4) is True
