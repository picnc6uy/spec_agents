"""Generic critic primitive (SA-002, library-mode).

The critic is a forced-tool-use Anthropic call that asks a model to review a
prior artifact and return a structured verdict. Domain-agnostic: the caller
supplies the rules (system prompt), the artifact-under-review (user prompt),
optional reference material (lens content, cached at the system layer), and
the verdict schema. The kernel handles the LLM call, system-block
construction, lens caching, and tool-output parsing.

Library mode (per the v2 charter): this is a plain function agents call.
No state, no scheduling, no autonomous orchestration. The caller composes.

Typical usage (consumer side):

    from anthropic import Anthropic
    from spec_agents.agents.critic import critique

    client = Anthropic(api_key=...)
    tool_input = critique(
        client=client,
        model="claude-sonnet-4-6",
        system_prompt=MY_RULES,
        user_prompt=build_user_prompt(artifact, lineage),
        lens_content=load_lenses(["calibration", ...]),
        verdict_schema=MY_SCHEMA,
        verdict_tool_name="submit_critique",
    )
    if tool_input is None:
        # API failure or no tool call. Caller decides retry / fallback.
        return None
    return MyVerdict(**tool_input)
"""

from __future__ import annotations

from typing import Any, cast

import anthropic
import structlog
from anthropic.types import ToolUseBlock

log = structlog.get_logger()


def critique(
    *,
    client: anthropic.Anthropic,
    model: str,
    system_prompt: str,
    user_prompt: str,
    verdict_schema: dict[str, Any],
    verdict_tool_name: str,
    lens_content: str | None = None,
    max_tokens: int = 3072,
    cache_lenses: bool = True,
) -> dict[str, Any] | None:
    """Run one forced-tool-use critique pass.

    Args:
        client: A pre-constructed Anthropic client. The caller owns the
            api_key plumbing; the kernel does not see credentials.
        model: Model identifier (e.g. ``claude-sonnet-4-6``).
        system_prompt: The rules the critic enforces — domain-specific.
            Goes in the first system content block.
        user_prompt: The artifact under review, plus any lineage / evidence
            context. Goes in a single user message.
        verdict_schema: JSON schema for the tool input. The model is forced
            to call the tool named ``verdict_tool_name`` with input matching
            this schema. The returned dict is the parsed tool input.
        verdict_tool_name: Name passed to the forced ``tool_choice``.
        lens_content: Optional reference text (e.g. lens output). Placed in
            a second system content block; cached when ``cache_lenses`` is
            True so repeated calls within the cache TTL pay ~10× less.
        max_tokens: Response token budget. Default 3072.
        cache_lenses: If True (default), add ``cache_control`` to the lens
            system block.

    Returns:
        Parsed tool input as a dict on success.
        ``None`` if the API call raised, or the response didn't contain a
        tool-use block for ``verdict_tool_name``. The caller decides what
        to do on None (retry, fallback verdict, abort).

    Design notes:
        - Forced tool use (``tool_choice={"type": "tool", ...}``) so the
          response is always structured. The v2 charter commits to single
          forced tool use as the discipline.
        - System blocks: rules first (small, stable), lens content second
          (large, optionally cacheable). Anthropic's prompt cache key is the
          full block prefix, so this ordering maximizes hit rate when only
          the user prompt changes.
        - Errors are caught here and logged; the caller sees ``None``. This
          matches the existing pattern in spectacular's brief_critic.py.
    """
    system_blocks: list[dict[str, Any]] = [
        {"type": "text", "text": system_prompt},
    ]
    if lens_content:
        block: dict[str, Any] = {"type": "text", "text": lens_content}
        if cache_lenses:
            block["cache_control"] = {"type": "ephemeral"}
        system_blocks.append(block)

    tools: list[dict[str, Any]] = [
        {
            "name": verdict_tool_name,
            "description": "Submit the structured critique using the schema below.",
            "input_schema": verdict_schema,
        }
    ]

    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_blocks,  # pyright: ignore[reportArgumentType]
            messages=[{"role": "user", "content": user_prompt}],
            tools=tools,  # pyright: ignore[reportArgumentType]
            tool_choice={"type": "tool", "name": verdict_tool_name},
        )
    except Exception as exc:
        log.error("critic.api_failed", error=str(exc), model=model)
        return None

    for block in response.content:
        # Duck-typed check (works with the SDK's discriminated-union content
        # blocks *and* with simple test stubs). pyright is told via cast that
        # this branch is a ToolUseBlock.
        if (
            getattr(block, "type", None) == "tool_use"
            and getattr(block, "name", None) == verdict_tool_name
        ):
            tool_block = cast(ToolUseBlock, block)
            return dict(tool_block.input)  # pyright: ignore[arg-type]

    log.warning("critic.no_tool_call", model=model, verdict_tool_name=verdict_tool_name)
    return None
