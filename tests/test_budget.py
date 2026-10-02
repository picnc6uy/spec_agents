"""Tests for spec_agents.budget: workers(), below_normal(), and the pool defaults."""

from __future__ import annotations

import os
import subprocess
import sys
import types
from pathlib import Path
from typing import Any

import pytest

from spec_agents import budget, caching
from spec_agents.agents import parallel

SRC = str(Path(__file__).resolve().parents[1] / "src")


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SPEC_AGENTS_WORKERS", raising=False)


# --- P1: workers() -----------------------------------------------------------


@pytest.mark.parametrize(("cpus", "expected"), [(12, 8), (5, 1), (1, 1), (None, 1)])
def test_workers_cap_and_floor(monkeypatch: pytest.MonkeyPatch, cpus: int | None, expected: int):
    monkeypatch.setattr("os.cpu_count", lambda: cpus)
    assert budget.workers() == expected


def test_workers_argument_beats_variable(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SPEC_AGENTS_WORKERS", "3")
    assert budget.workers(7) == 7


def test_workers_variable_beats_cap(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("os.cpu_count", lambda: 12)
    monkeypatch.setenv("SPEC_AGENTS_WORKERS", "3")
    assert budget.workers() == 3


def test_workers_blank_variable_ignored(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("os.cpu_count", lambda: 12)
    monkeypatch.setenv("SPEC_AGENTS_WORKERS", "   ")
    assert budget.workers() == 8


@pytest.mark.parametrize("bad", ["0", "-1", "abc"])
def test_workers_bad_variable_raises(monkeypatch: pytest.MonkeyPatch, bad: str):
    monkeypatch.setenv("SPEC_AGENTS_WORKERS", bad)
    with pytest.raises(ValueError, match="SPEC_AGENTS_WORKERS"):
        budget.workers()


@pytest.mark.parametrize("bad", [0, -1])
def test_workers_bad_argument_raises(bad: int):
    with pytest.raises(ValueError, match="workers"):
        budget.workers(bad)


# --- P2: below_normal() ------------------------------------------------------


def _fake_nice(state: dict[str, int]) -> Any:
    def nice(inc: int) -> int:
        state["nice"] += inc
        return state["nice"]

    return nice


def test_posix_raises_niceness_once(monkeypatch: pytest.MonkeyPatch):
    state = {"nice": 0}
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr("os.nice", _fake_nice(state), raising=False)
    assert budget.below_normal() is True
    assert state["nice"] == 10
    assert budget.below_normal() is True
    assert state["nice"] == 10


def test_posix_never_moves_upward(monkeypatch: pytest.MonkeyPatch):
    state = {"nice": 15}
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr("os.nice", _fake_nice(state), raising=False)
    assert budget.below_normal() is True
    assert state["nice"] == 15


def test_posix_refusal_returns_false(monkeypatch: pytest.MonkeyPatch):
    def refuse(inc: int) -> int:
        raise PermissionError("no")

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr("os.nice", refuse, raising=False)
    assert budget.below_normal() is False


def test_unknown_platform_returns_false(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sys, "platform", "plan9")
    assert budget.below_normal() is False


class _FakeProc:
    def __init__(self, cls: int, fail: bool = False) -> None:
        self.cls = cls
        self.fail = fail

    def nice(self, value: int | None = None) -> int | None:
        if value is None:
            return self.cls
        if self.fail:
            raise OSError("access denied")
        self.cls = value
        return None


def _fake_psutil(proc: _FakeProc) -> Any:
    return types.SimpleNamespace(Process=lambda: proc)


def test_windows_psutil_sets_below_normal(monkeypatch: pytest.MonkeyPatch):
    proc = _FakeProc(0x20)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "psutil", _fake_psutil(proc))
    assert budget.below_normal() is True
    assert proc.cls == 0x4000
    assert budget.below_normal() is True
    assert proc.cls == 0x4000


@pytest.mark.parametrize("already", [0x40, 0x4000])
def test_windows_psutil_never_moves_upward(monkeypatch: pytest.MonkeyPatch, already: int):
    proc = _FakeProc(already)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "psutil", _fake_psutil(proc))
    assert budget.below_normal() is True
    assert proc.cls == already


def test_windows_psutil_refusal_returns_false(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "psutil", _fake_psutil(_FakeProc(0x20, fail=True)))
    assert budget.below_normal() is False


class _FakeKernel32:
    def __init__(self, cls: int, set_result: int = 1) -> None:
        self.cls = cls
        self.set_result = set_result
        self.set_calls = 0

    def GetPriorityClass(self, handle: object) -> int:  # noqa: N802
        return self.cls

    def SetPriorityClass(self, handle: object, value: int) -> int:  # noqa: N802
        self.set_calls += 1
        if self.set_result:
            self.cls = value
        return self.set_result


def _use_ctypes(monkeypatch: pytest.MonkeyPatch, kernel: _FakeKernel32) -> None:
    import ctypes

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "psutil", None)  # forces ImportError
    monkeypatch.setattr(ctypes, "windll", types.SimpleNamespace(kernel32=kernel), raising=False)


def test_windows_ctypes_sets_below_normal(monkeypatch: pytest.MonkeyPatch):
    kernel = _FakeKernel32(0x20)
    _use_ctypes(monkeypatch, kernel)
    assert budget.below_normal() is True
    assert kernel.cls == 0x4000
    assert budget.below_normal() is True
    assert kernel.set_calls == 1


def test_windows_ctypes_never_moves_upward(monkeypatch: pytest.MonkeyPatch):
    kernel = _FakeKernel32(0x40)
    _use_ctypes(monkeypatch, kernel)
    assert budget.below_normal() is True
    assert kernel.set_calls == 0


def test_windows_ctypes_zero_return_is_false(monkeypatch: pytest.MonkeyPatch):
    _use_ctypes(monkeypatch, _FakeKernel32(0x20, set_result=0))
    assert budget.below_normal() is False


_CHILD = """
import sys
from spec_agents import budget

def read():
    if sys.platform == "win32":
        import ctypes
        k = ctypes.windll.kernel32
        return hex(k.GetPriorityClass(ctypes.c_void_p(-1)))
    import os
    return os.nice(0)

r1 = budget.below_normal(); a = read()
r2 = budget.below_normal(); b = read()
print(r1, r2, a, b)
"""


def test_below_normal_real_process_twice():
    out = subprocess.run(
        [sys.executable, "-c", _CHILD],
        env={**os.environ, "PYTHONPATH": SRC},
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    ).stdout.split()
    r1, r2, a, b = out
    assert (r1, r2) == ("True", "True")
    assert a == b
    if sys.platform == "win32":
        assert a in ("0x40", "0x4000")  # an IDLE parent is correctly left alone
    else:
        assert int(a) >= 10


# --- P3: pool defaults -------------------------------------------------------


def _record_pool(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    seen: list[int] = []
    real = caching.ThreadPoolExecutor

    def spy(max_workers: int | None = None, **kw: Any) -> Any:
        assert max_workers is not None
        seen.append(max_workers)
        return real(max_workers=max_workers, **kw)

    monkeypatch.setattr(caching, "ThreadPoolExecutor", spy)
    return seen


class _Client:
    class messages:  # noqa: N801
        @staticmethod
        def create(**kw: Any) -> Any:
            return types.SimpleNamespace(
                content="x",
                usage=types.SimpleNamespace(
                    input_tokens=1,
                    output_tokens=1,
                    cache_creation_input_tokens=0,
                    cache_read_input_tokens=0,
                ),
            )


def _map(max_workers: int | None) -> Any:
    kwargs: dict[str, Any] = {} if max_workers is None else {"max_workers": max_workers}
    return parallel.map_agent(
        client=_Client(),
        items=list(range(5)),
        shared_system_text="s",
        build_user_content=lambda i: str(i),
        parse=lambda r: r.content,
        warm=False,
        **kwargs,
    )


def test_warm_then_fan_out_default_uses_budget(monkeypatch: pytest.MonkeyPatch):
    seen = _record_pool(monkeypatch)
    monkeypatch.setenv("SPEC_AGENTS_WORKERS", "2")
    caching.warm_then_fan_out(list(range(5)), lambda x: x, warm=False)
    assert seen == [2]


def test_warm_then_fan_out_explicit_wins(monkeypatch: pytest.MonkeyPatch):
    seen = _record_pool(monkeypatch)
    monkeypatch.setenv("SPEC_AGENTS_WORKERS", "2")
    caching.warm_then_fan_out(list(range(5)), lambda x: x, max_workers=4, warm=False)
    assert seen == [4]


def test_map_agent_default_uses_budget(monkeypatch: pytest.MonkeyPatch):
    seen = _record_pool(monkeypatch)
    monkeypatch.setenv("SPEC_AGENTS_WORKERS", "2")
    _map(None)
    assert seen == [2]


def test_map_agent_explicit_wins(monkeypatch: pytest.MonkeyPatch):
    seen = _record_pool(monkeypatch)
    monkeypatch.setenv("SPEC_AGENTS_WORKERS", "2")
    _map(4)
    assert seen == [4]


def test_bad_variable_fails_before_warm_call(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SPEC_AGENTS_WORKERS", "abc")
    calls: list[int] = []
    with pytest.raises(ValueError, match="SPEC_AGENTS_WORKERS"):
        caching.warm_then_fan_out([1, 2, 3], calls.append, warm=True)
    assert calls == []


@pytest.mark.parametrize("bad", [True, 2.9, float("inf")])
def test_workers_rejects_bool_and_float(bad: object):
    with pytest.raises(ValueError, match="workers"):
        budget.workers(bad)  # type: ignore[arg-type]
