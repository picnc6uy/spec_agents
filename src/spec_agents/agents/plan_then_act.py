"""Plan-then-act orchestration (library-mode, SA-004).

Two forced-tool-use calls in sequence:

1. **Plan**: ask the model to produce a structured plan (e.g. "what
   are the steps", "which precedents do I lean on", "what's my
   strategy"). The plan is returned as a typed dict via forced tool.
2. **Execute**: build a user prompt from the plan and ask the model to
   produce the actual decision / output / artifact, again via forced
   tool use.

Why two calls instead of one: per the v2 charter's "leftward shift"
discipline, splitting plan from execution makes each call's inputs
tighter and the failure modes visible. Spectacular's single-call
synthesizer doesn't need this — its inputs are already small and
focused. Photo_archive's match decisions do — the model needs to first
choose how to weigh evidence (plan), then apply the chosen scheme to
the candidates (execute).

This module is a composition of two `critic.critique` calls; no new
LLM-orchestration code lives here. The kernel surface is small on
purpose — library-mode means each primitive is a plain function the
caller composes.

Typical consumer (sketch — exact prompts/schemas are domain-specific):

    from anthropic import Anthropic
    from spec_agents.agents.plan_then_act import plan_then_act

    client = Anthropic(api_key=...)

    result = plan_then_act(
        client=client,
        model="claude-opus-4-7",
        plan_system_prompt=MATCH_PLAN_RULES,
        plan_user_prompt=build_plan_prompt(candidate, evidence),
        plan_schema=MATCH_PLAN_SCHEMA,
        plan_tool_name="submit_plan",
        execute_system_prompt=MATCH_DECIDE_RULES,
        execute_user_prompt_builder=lambda plan: build_decide_prompt(
            candidate, evidence, plan
        ),
        execute_schema=MATCH_DECISION_SCHEMA,
        execute_tool_name="submit_decision",
    )
    if result.plan is None or result.execution is None:
        # one of the two calls failed; consumer decides fallback
        ...
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import anthropic
import structlog

from spec_agents.agents.critic import critique

log = structlog.get_logger()


@dataclass(frozen=True)
class PlanThenActResult:
    """Outcome of one plan-then-act invocation.

    ``plan`` carries the parsed tool-input dict from the plan call;
    ``execution`` carries the parsed tool-input dict from the execute
    call. Either can be ``None`` if its call failed or returned no
    matching tool block. ``execution`` is always ``None`` when ``plan``
    is — the orchestrator does not attempt to execute against a missing
    plan.
    """

    plan: dict[str, Any] | None
    execution: dict[str, Any] | None


# Builder shape: the execute phase needs the plan dict to compose its
# user prompt. The caller provides this closure.
ExecutePromptBuilder = Callable[[dict[str, Any]], str]


def plan_then_act(
    *,
    client: anthropic.Anthropic,
    model: str,
    # Plan phase.
    plan_system_prompt: str,
    plan_user_prompt: str,
    plan_schema: dict[str, Any],
    plan_tool_name: str,
    # Execute phase.
    execute_system_prompt: str,
    execute_user_prompt_builder: ExecutePromptBuilder,
    execute_schema: dict[str, Any],
    execute_tool_name: str,
    # Shared.
    lens_content: str | None = None,
    max_tokens: int = 4096,
) -> PlanThenActResult:
    """Two-call orchestration: plan via forced tool use, then execute.

    Args:
        client: Pre-constructed Anthropic client.
        model: Model identifier used for both calls. Use the same model
            for both unless you have a specific reason to mix.
        plan_system_prompt: Rules / constraints for the plan phase.
        plan_user_prompt: Artifact + context for the plan phase.
        plan_schema: JSON schema for the plan's tool input.
        plan_tool_name: Forced tool-choice name for the plan phase.
        execute_system_prompt: Rules / constraints for the execute phase.
        execute_user_prompt_builder: Callable taking the plan dict and
            returning the user prompt for the execute phase. This is
            how the plan gets re-injected as context (the v2 charter's
            "leftward shift" — local Python decides what the model sees
            for the second call).
        execute_schema: JSON schema for the execute phase's tool input.
        execute_tool_name: Forced tool-choice name for the execute phase.
        lens_content: Optional cached lens content for the plan phase.
            (The execute phase does not get lenses by default — the
            plan already carries the focused context. If a consumer
            needs both, they can include lens material in their
            ``execute_system_prompt`` directly.)
        max_tokens: Per-call token budget. Default 4096.

    Returns:
        ``PlanThenActResult(plan, execution)``. Either can be ``None``;
        if ``plan`` is ``None`` the execute phase is skipped and
        ``execution`` is also ``None``.
    """
    plan = critique(
        client=client,
        model=model,
        system_prompt=plan_system_prompt,
        user_prompt=plan_user_prompt,
        verdict_schema=plan_schema,
        verdict_tool_name=plan_tool_name,
        lens_content=lens_content,
        max_tokens=max_tokens,
    )
    if plan is None:
        log.warning("plan_then_act.plan_failed", model=model)
        return PlanThenActResult(plan=None, execution=None)

    execute_user_prompt = execute_user_prompt_builder(plan)
    execution = critique(
        client=client,
        model=model,
        system_prompt=execute_system_prompt,
        user_prompt=execute_user_prompt,
        verdict_schema=execute_schema,
        verdict_tool_name=execute_tool_name,
        lens_content=None,
        max_tokens=max_tokens,
    )
    if execution is None:
        log.warning("plan_then_act.execute_failed", model=model)

    return PlanThenActResult(plan=plan, execution=execution)
