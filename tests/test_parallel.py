"""Tests for spec_agents.agents.parallel.map_agent (fake client, no real API)."""

from __future__ import annotations

import threading
from types import SimpleNamespace
from typing import Any

from spec_agents.agents.parallel import (
    DEFAULT_PARALLEL_MODEL,
    MapResult,
    map_agent,
)


def _usage(*, inp: int = 10, out: int = 5, cc: int = 0, cr: int = 0) -> SimpleNamespace:
    return SimpleNamespace(
        input_tokens=inp,
        output_tokens=out,
        cache_creation_input_tokens=cc,
        cache_read_input_tokens=cr,
    )


class _FakeMessages:
    """Echoes the user content back into the response so tests can assert order,
    and returns a configurable usage object per call."""

    def __init__(self, usage_factory: Any = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self._usage_factory = usage_factory or (lambda _user: _usage())

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        user = kwargs["messages"][0]["content"]
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=f"echo:{user}")],
            usage=self._usage_factory(user),
        )


class _FakeClient:
    def __init__(self, usage_factory: Any = None) -> None:
        self.messages = _FakeMessages(usage_factory)


def _parse_echo(response: Any) -> str:
    return str(response.content[0].text)


# ── results / ordering ──────────────────────────────────────────────────


def test_map_agent_returns_results_in_item_order() -> None:
    client = _FakeClient()
    result = map_agent(
        client=client,
        items=[1, 2, 3, 4],
        shared_system_text="CTX",
        build_user_content=lambda i: f"item-{i}",
        parse=_parse_echo,
        max_workers=4,
    )
    assert isinstance(result, MapResult)
    assert result.results == ["echo:item-1", "echo:item-2", "echo:item-3", "echo:item-4"]


def test_map_agent_empty_items() -> None:
    client = _FakeClient()
    result = map_agent(
        client=client,
        items=[],
        shared_system_text="CTX",
        build_user_content=lambda i: str(i),
        parse=_parse_echo,
    )
    assert result.results == []
    assert result.usage.calls == 0
    assert result.usage.cost_usd == 0.0
    assert result.usage.churning is False


# ── prompt assembly: cached shared prefix, variable user turn ────────────


def test_shared_system_is_cached_block_and_not_duplicated_per_item() -> None:
    client = _FakeClient()
    map_agent(
        client=client,
        items=["a", "b"],
        shared_system_text="BIG_SHARED_CORPUS",
        build_user_content=lambda i: f"ask about {i}",
        parse=_parse_echo,
    )
    for call in client.messages.calls:
        system = call["system"]
        assert isinstance(system, list) and len(system) == 1
        assert system[0]["cache_control"] == {"type": "ephemeral"}
        assert system[0]["text"] == "BIG_SHARED_CORPUS"
        # The big shared corpus must NOT be duplicated into the per-item user turn.
        assert "BIG_SHARED_CORPUS" not in call["messages"][0]["content"]


def test_default_model_is_haiku_and_overridable() -> None:
    client = _FakeClient()
    map_agent(
        client=client,
        items=["x"],
        shared_system_text="c",
        build_user_content=lambda i: i,
        parse=_parse_echo,
    )
    assert (
        client.messages.calls[0]["model"] == DEFAULT_PARALLEL_MODEL == "claude-haiku-4-5-20251001"
    )

    client2 = _FakeClient()
    map_agent(
        client=client2,
        items=["x"],
        shared_system_text="c",
        build_user_content=lambda i: i,
        parse=_parse_echo,
        model="claude-sonnet-4-6",
    )
    assert client2.messages.calls[0]["model"] == "claude-sonnet-4-6"


def test_tools_and_tool_choice_passthrough_only_when_provided() -> None:
    # Not provided → keys absent.
    client = _FakeClient()
    map_agent(
        client=client,
        items=["x"],
        shared_system_text="c",
        build_user_content=lambda i: i,
        parse=_parse_echo,
    )
    assert "tools" not in client.messages.calls[0]
    assert "tool_choice" not in client.messages.calls[0]

    # Provided → forwarded verbatim.
    client2 = _FakeClient()
    tools = [{"name": "t", "input_schema": {"type": "object"}}]
    choice = {"type": "any"}
    map_agent(
        client=client2,
        items=["x"],
        shared_system_text="c",
        build_user_content=lambda i: i,
        parse=_parse_echo,
        tools=tools,
        tool_choice=choice,
    )
    assert client2.messages.calls[0]["tools"] == tools
    assert client2.messages.calls[0]["tool_choice"] == choice


# ── usage aggregation + churn ────────────────────────────────────────────


def test_usage_aggregates_across_the_fanout() -> None:
    # Fixed usage per call: input=10, output=5, cache_read=50. 4 items.
    client = _FakeClient(usage_factory=lambda _u: _usage(inp=10, out=5, cr=50))
    result = map_agent(
        client=client,
        items=[1, 2, 3, 4],
        shared_system_text="c",
        build_user_content=lambda i: str(i),
        parse=_parse_echo,
        model="claude-haiku-4-5-20251001",
    )
    u = result.usage
    assert u.calls == 4
    assert u.input_tokens == 40
    assert u.output_tokens == 20
    assert u.cache_read_tokens == 200
    assert u.cache_creation_tokens == 0
    # cost = (40*1.0 + 20*5.0 + 200*0.10) / 1e6 at Haiku 4.5 rates ($1/$5, read $0.10)
    expected = (40 * 1.0 + 20 * 5.0 + 200 * 0.10) / 1_000_000
    assert abs(u.cost_usd - expected) < 1e-12
    assert u.churning is False  # no creation → not churning


def test_churning_flag_set_when_creation_dwarfs_reads() -> None:
    # Each call re-creates the prefix (cc) and barely reads — the storm signature.
    client = _FakeClient(usage_factory=lambda _u: _usage(inp=10, out=5, cc=130_000, cr=0))
    result = map_agent(
        client=client,
        items=[1, 2, 3],
        shared_system_text="c",
        build_user_content=lambda i: str(i),
        parse=_parse_echo,
    )
    assert result.usage.cache_creation_tokens == 390_000
    assert result.usage.churning is True


# ── warm-then-fan-out at this layer ──────────────────────────────────────


def test_warm_completes_before_fanout_starts() -> None:
    warmed = threading.Event()
    violations: list[str] = []

    def usage_factory(user: str) -> SimpleNamespace:
        if user == "warm":
            warmed.set()
        else:
            if not warmed.is_set():
                violations.append(user)
        return _usage()

    client = _FakeClient(usage_factory=usage_factory)
    items = ["warm", "f1", "f2", "f3", "f4"]
    result = map_agent(
        client=client,
        items=items,
        shared_system_text="c",
        build_user_content=lambda i: i,
        parse=_parse_echo,
        max_workers=4,
        warm=True,
    )
    assert result.results == [f"echo:{i}" for i in items]
    assert violations == [], f"fan-out items processed before warm-up landed: {violations}"
