"""Smoke tests for spec_agents.agents.critic.

The kernel test uses a stub Anthropic client. Live-API behavior is exercised
by consumers (spectacular's brief_critic regression suite).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from spec_agents.agents.critic import critique


@dataclass
class _StubBlock:
    type: str
    name: str | None = None
    input: dict[str, Any] | None = None


@dataclass
class _StubResponse:
    content: list[_StubBlock]


class _StubClient:
    """Mimics the slice of anthropic.Anthropic that critique() touches."""

    def __init__(self, response: _StubResponse | None = None, raises: Exception | None = None):
        self._response = response
        self._raises = raises
        self.last_call: dict[str, Any] | None = None

    class _Messages:
        def __init__(self, parent: _StubClient):
            self._parent = parent

        def create(self, **kwargs: Any) -> Any:
            self._parent.last_call = kwargs
            if self._parent._raises is not None:
                raise self._parent._raises
            return self._parent._response

    @property
    def messages(self) -> _StubClient._Messages:
        return _StubClient._Messages(self)


_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string"},
        "issues": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["verdict", "issues"],
}


def _make_response(
    tool_input: dict[str, Any] | None, *, tool_name: str = "submit_critique"
) -> _StubResponse:
    if tool_input is None:
        return _StubResponse(content=[_StubBlock(type="text")])
    return _StubResponse(content=[_StubBlock(type="tool_use", name=tool_name, input=tool_input)])


def test_critique_returns_parsed_tool_input() -> None:
    client = _StubClient(response=_make_response({"verdict": "approved", "issues": []}))
    result = critique(
        client=client,  # type: ignore[arg-type]
        model="claude-sonnet-4-6",
        system_prompt="be strict",
        user_prompt="review this",
        verdict_schema=_SCHEMA,
        verdict_tool_name="submit_critique",
    )
    assert result == {"verdict": "approved", "issues": []}


def test_critique_forces_the_named_tool() -> None:
    client = _StubClient(response=_make_response({"verdict": "approved", "issues": []}))
    critique(
        client=client,  # type: ignore[arg-type]
        model="claude-sonnet-4-6",
        system_prompt="rules",
        user_prompt="user",
        verdict_schema=_SCHEMA,
        verdict_tool_name="submit_review",
    )
    assert client.last_call is not None
    assert client.last_call["tool_choice"] == {"type": "tool", "name": "submit_review"}
    tool = client.last_call["tools"][0]
    assert tool["name"] == "submit_review"
    assert tool["input_schema"] == _SCHEMA


def test_critique_adds_cached_lens_block() -> None:
    client = _StubClient(response=_make_response({"verdict": "approved", "issues": []}))
    critique(
        client=client,  # type: ignore[arg-type]
        model="claude-sonnet-4-6",
        system_prompt="rules",
        user_prompt="user",
        verdict_schema=_SCHEMA,
        verdict_tool_name="submit_critique",
        lens_content="reference content",
    )
    assert client.last_call is not None
    system = client.last_call["system"]
    assert len(system) == 2
    assert system[0] == {"type": "text", "text": "rules"}
    assert system[1]["text"] == "reference content"
    assert system[1]["cache_control"] == {"type": "ephemeral"}


def test_critique_can_disable_lens_cache() -> None:
    client = _StubClient(response=_make_response({"verdict": "approved", "issues": []}))
    critique(
        client=client,  # type: ignore[arg-type]
        model="claude-sonnet-4-6",
        system_prompt="rules",
        user_prompt="user",
        verdict_schema=_SCHEMA,
        verdict_tool_name="submit_critique",
        lens_content="reference content",
        cache_lenses=False,
    )
    assert client.last_call is not None
    system = client.last_call["system"]
    assert "cache_control" not in system[1]


def test_critique_lens_first_puts_cached_lens_before_rules() -> None:
    client = _StubClient(response=_make_response({"verdict": "approved", "issues": []}))
    critique(
        client=client,  # type: ignore[arg-type]
        model="claude-opus-4-8",
        system_prompt="rules",
        user_prompt="user",
        verdict_schema=_SCHEMA,
        verdict_tool_name="submit_critique",
        lens_content="THE CORPUS",
        lens_first=True,
    )
    assert client.last_call is not None
    system = client.last_call["system"]
    assert len(system) == 2
    # Lens leads (and is the cached block); rules follow.
    assert system[0]["text"] == "THE CORPUS"
    assert system[0]["cache_control"] == {"type": "ephemeral"}
    assert system[1] == {"type": "text", "text": "rules"}


def test_critique_lens_first_shares_one_lens_block_across_differing_rules() -> None:
    """A synthesizer and its paired challenger over one corpus: different rules,
    same cached lens block → the corpus cache is shared."""
    synth = _StubClient(response=_make_response({"verdict": "ok", "issues": []}))
    chall = _StubClient(response=_make_response({"verdict": "ok", "issues": []}))
    common = dict(
        model="claude-opus-4-8",
        user_prompt="artifact",
        verdict_schema=_SCHEMA,
        verdict_tool_name="submit_critique",
        lens_content="ONE-SHARED-CORPUS",
        lens_first=True,
    )
    critique(client=synth, system_prompt="SYNTHESIZE the findings", **common)  # type: ignore[arg-type]
    critique(client=chall, system_prompt="CHALLENGE the draft", **common)  # type: ignore[arg-type]
    assert synth.last_call is not None and chall.last_call is not None
    assert synth.last_call["system"][0] == chall.last_call["system"][0]


def test_critique_lens_first_noop_without_lens_content() -> None:
    client = _StubClient(response=_make_response({"verdict": "approved", "issues": []}))
    critique(
        client=client,  # type: ignore[arg-type]
        model="claude-opus-4-8",
        system_prompt="rules",
        user_prompt="user",
        verdict_schema=_SCHEMA,
        verdict_tool_name="submit_critique",
        lens_first=True,
    )
    assert client.last_call is not None
    assert client.last_call["system"] == [{"type": "text", "text": "rules"}]


def test_critique_default_order_is_rules_then_lens() -> None:
    """lens_first defaults False → original rules-first ordering is preserved."""
    client = _StubClient(response=_make_response({"verdict": "approved", "issues": []}))
    critique(
        client=client,  # type: ignore[arg-type]
        model="claude-sonnet-4-6",
        system_prompt="rules",
        user_prompt="user",
        verdict_schema=_SCHEMA,
        verdict_tool_name="submit_critique",
        lens_content="ref",
    )
    assert client.last_call is not None
    system = client.last_call["system"]
    assert system[0] == {"type": "text", "text": "rules"}
    assert system[1]["text"] == "ref"


def test_critique_returns_none_on_api_error() -> None:
    client = _StubClient(raises=RuntimeError("rate limit"))
    result = critique(
        client=client,  # type: ignore[arg-type]
        model="claude-sonnet-4-6",
        system_prompt="rules",
        user_prompt="user",
        verdict_schema=_SCHEMA,
        verdict_tool_name="submit_critique",
    )
    assert result is None


def test_critique_returns_none_when_no_tool_call() -> None:
    client = _StubClient(response=_make_response(None))
    result = critique(
        client=client,  # type: ignore[arg-type]
        model="claude-sonnet-4-6",
        system_prompt="rules",
        user_prompt="user",
        verdict_schema=_SCHEMA,
        verdict_tool_name="submit_critique",
    )
    assert result is None


def test_critique_ignores_blocks_for_other_tools() -> None:
    """Defensive: if the response has multiple tool-use blocks, the one
    matching verdict_tool_name wins."""
    client = _StubClient(
        response=_StubResponse(
            content=[
                _StubBlock(type="tool_use", name="other_tool", input={"x": 1}),
                _StubBlock(type="tool_use", name="submit_critique", input={"verdict": "x"}),
            ]
        )
    )
    result = critique(
        client=client,  # type: ignore[arg-type]
        model="claude-sonnet-4-6",
        system_prompt="rules",
        user_prompt="user",
        verdict_schema=_SCHEMA,
        verdict_tool_name="submit_critique",
    )
    assert result == {"verdict": "x"}
