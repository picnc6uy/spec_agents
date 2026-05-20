"""Smoke tests for spec_agents.agents.plan_then_act (SA-004).

Uses a stub Anthropic client. Live behavior is exercised by consumers
(photo_archive match decisions once D-4 lands and the matcher is built).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from spec_agents.agents.plan_then_act import PlanThenActResult, plan_then_act

# ── Stub Anthropic client ──────────────────────────────────────────────


@dataclass
class _StubBlock:
    type: str
    name: str | None = None
    input: dict[str, Any] | None = None


@dataclass
class _StubResponse:
    content: list[_StubBlock]


class _StubClient:
    """Records every messages.create call; returns from a per-call queue."""

    def __init__(self) -> None:
        self.responses: list[_StubResponse] = []
        self.raises: list[Exception | None] = []
        self.calls: list[dict[str, Any]] = []

    def queue(self, response: _StubResponse | None, raises: Exception | None = None) -> None:
        self.responses.append(response or _StubResponse(content=[]))
        self.raises.append(raises)

    class _Messages:
        def __init__(self, parent: _StubClient) -> None:
            self._parent = parent

        def create(self, **kwargs: Any) -> Any:
            idx = len(self._parent.calls)
            self._parent.calls.append(kwargs)
            if idx >= len(self._parent.responses):
                raise AssertionError(f"unexpected extra call (#{idx + 1})")
            raises = self._parent.raises[idx]
            if raises is not None:
                raise raises
            return self._parent.responses[idx]

    @property
    def messages(self) -> _StubClient._Messages:
        return _StubClient._Messages(self)


def _tool_response(tool_name: str, payload: dict[str, Any]) -> _StubResponse:
    return _StubResponse(content=[_StubBlock(type="tool_use", name=tool_name, input=payload)])


# ── Tests ──────────────────────────────────────────────────────────────


_PLAN_SCHEMA = {
    "type": "object",
    "properties": {"strategy": {"type": "string"}, "weights": {"type": "object"}},
    "required": ["strategy"],
}

_EXEC_SCHEMA = {
    "type": "object",
    "properties": {"decision": {"type": "string"}, "confidence": {"type": "number"}},
    "required": ["decision"],
}


def test_plan_then_act_happy_path() -> None:
    client = _StubClient()
    client.queue(_tool_response("submit_plan", {"strategy": "weight_funding_heavy"}))
    client.queue(_tool_response("submit_decision", {"decision": "bullish", "confidence": 0.7}))

    captured_plans: list[dict[str, Any]] = []

    def build_execute_prompt(plan: dict[str, Any]) -> str:
        captured_plans.append(plan)
        return f"Execute per plan: {plan['strategy']}"

    result = plan_then_act(
        client=client,  # type: ignore[arg-type]
        model="claude-opus-4-7",
        plan_system_prompt="You produce match plans.",
        plan_user_prompt="Plan a match for candidate X.",
        plan_schema=_PLAN_SCHEMA,
        plan_tool_name="submit_plan",
        execute_system_prompt="You execute match plans.",
        execute_user_prompt_builder=build_execute_prompt,
        execute_schema=_EXEC_SCHEMA,
        execute_tool_name="submit_decision",
    )

    assert isinstance(result, PlanThenActResult)
    assert result.plan == {"strategy": "weight_funding_heavy"}
    assert result.execution == {"decision": "bullish", "confidence": 0.7}
    assert captured_plans == [{"strategy": "weight_funding_heavy"}]


def test_plan_then_act_skips_execute_when_plan_fails() -> None:
    """If the plan call returns no tool use (empty content), execute
    should not be attempted."""
    client = _StubClient()
    client.queue(_StubResponse(content=[]))  # plan: no tool call

    def must_not_call(plan: dict[str, Any]) -> str:
        raise AssertionError("execute_user_prompt_builder should not be called")

    result = plan_then_act(
        client=client,  # type: ignore[arg-type]
        model="m",
        plan_system_prompt="P",
        plan_user_prompt="P",
        plan_schema=_PLAN_SCHEMA,
        plan_tool_name="submit_plan",
        execute_system_prompt="E",
        execute_user_prompt_builder=must_not_call,
        execute_schema=_EXEC_SCHEMA,
        execute_tool_name="submit_decision",
    )

    assert result.plan is None
    assert result.execution is None
    assert len(client.calls) == 1  # plan only


def test_plan_then_act_carries_through_when_execute_fails() -> None:
    """If the execute call returns no tool use, plan is still returned."""
    client = _StubClient()
    client.queue(_tool_response("submit_plan", {"strategy": "default"}))
    client.queue(_StubResponse(content=[]))  # execute: no tool call

    result = plan_then_act(
        client=client,  # type: ignore[arg-type]
        model="m",
        plan_system_prompt="P",
        plan_user_prompt="P",
        plan_schema=_PLAN_SCHEMA,
        plan_tool_name="submit_plan",
        execute_system_prompt="E",
        execute_user_prompt_builder=lambda _plan: "execute prompt",
        execute_schema=_EXEC_SCHEMA,
        execute_tool_name="submit_decision",
    )

    assert result.plan == {"strategy": "default"}
    assert result.execution is None


def test_plan_then_act_forces_each_phase_distinct_tool() -> None:
    """The two calls force different tool names — verify both surfaces."""
    client = _StubClient()
    client.queue(_tool_response("submit_plan", {"strategy": "x"}))
    client.queue(_tool_response("submit_decision", {"decision": "y"}))

    plan_then_act(
        client=client,  # type: ignore[arg-type]
        model="claude-opus-4-7",
        plan_system_prompt="P",
        plan_user_prompt="P",
        plan_schema=_PLAN_SCHEMA,
        plan_tool_name="submit_plan",
        execute_system_prompt="E",
        execute_user_prompt_builder=lambda _plan: "go",
        execute_schema=_EXEC_SCHEMA,
        execute_tool_name="submit_decision",
    )

    assert client.calls[0]["tool_choice"] == {"type": "tool", "name": "submit_plan"}
    assert client.calls[1]["tool_choice"] == {"type": "tool", "name": "submit_decision"}
    # Plan tool schema went out in call 1; decision schema in call 2.
    assert client.calls[0]["tools"][0]["input_schema"] == _PLAN_SCHEMA
    assert client.calls[1]["tools"][0]["input_schema"] == _EXEC_SCHEMA


def test_plan_then_act_lens_content_goes_to_plan_call_only() -> None:
    """Plan call gets cached lens content; execute call does not."""
    client = _StubClient()
    client.queue(_tool_response("submit_plan", {"strategy": "x"}))
    client.queue(_tool_response("submit_decision", {"decision": "y"}))

    plan_then_act(
        client=client,  # type: ignore[arg-type]
        model="m",
        plan_system_prompt="P",
        plan_user_prompt="P",
        plan_schema=_PLAN_SCHEMA,
        plan_tool_name="submit_plan",
        execute_system_prompt="E",
        execute_user_prompt_builder=lambda _plan: "go",
        execute_schema=_EXEC_SCHEMA,
        execute_tool_name="submit_decision",
        lens_content="reference docs",
    )

    plan_system = client.calls[0]["system"]
    exec_system = client.calls[1]["system"]
    # Plan: 2 blocks (rules + cached lens).
    assert len(plan_system) == 2
    assert plan_system[1]["text"] == "reference docs"
    assert plan_system[1]["cache_control"] == {"type": "ephemeral"}
    # Execute: 1 block (just rules — no lens).
    assert len(exec_system) == 1
    assert exec_system[0]["text"] == "E"


def test_plan_then_act_execute_prompt_built_from_plan() -> None:
    """The user prompt for the execute call is what
    execute_user_prompt_builder returned."""
    client = _StubClient()
    client.queue(_tool_response("submit_plan", {"strategy": "agg", "weights": {"a": 1}}))
    client.queue(_tool_response("submit_decision", {"decision": "x"}))

    def builder(plan: dict[str, Any]) -> str:
        return f"Plan was {plan['strategy']}; weights {plan['weights']}"

    plan_then_act(
        client=client,  # type: ignore[arg-type]
        model="m",
        plan_system_prompt="P",
        plan_user_prompt="P",
        plan_schema=_PLAN_SCHEMA,
        plan_tool_name="submit_plan",
        execute_system_prompt="E",
        execute_user_prompt_builder=builder,
        execute_schema=_EXEC_SCHEMA,
        execute_tool_name="submit_decision",
    )

    exec_messages = client.calls[1]["messages"]
    assert exec_messages[0]["content"] == "Plan was agg; weights {'a': 1}"
