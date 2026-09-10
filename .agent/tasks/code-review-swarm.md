---
id: code-review-swarm
title: Corpus-first cache prefix for map_agent + critique (code-review-swarm foundation, sprint A)
type: new-feature
lens: new-feature
created: 2026-06-01
status: drafted
budget:
  # Soft caps the agent self-applies. On breach, do NOT grind on or fake green:
  # follow the escape-hatch contract in agent-task/RECOVERY.md.
  max_iterations: 25
  max_cost_usd: 3   # unit tests use stub clients; no live API required
  on_breach: abort-to-needs-rework
acceptance:
  - "map_agent gains optional kwarg `cached_prefix_text: str | None = None`."
  - "When cached_prefix_text is None, map_agent's `system` is byte-identical to today: `[cached_text_block(shared_system_text)]` (full backward compat)."
  - "When cached_prefix_text is provided, map_agent's `system` is `[cached_text_block(cached_prefix_text), {\"type\":\"text\",\"text\": shared_system_text}]` — cache_control ONLY on the leading prefix block; the trailing preamble block is uncached."
  - "critique gains optional kwarg `lens_first: bool = False`."
  - "When lens_first is False, critique's system_blocks ordering is unchanged: `[rules, (cached) lens]`."
  - "When lens_first is True AND lens_content is provided, the (cached) lens block precedes the rules block: `[(cached) lens, rules]`."
  - "Test: two map_agent calls with identical cached_prefix_text but DIFFERENT shared_system_text emit a byte-identical first system block (the cross-tier cache invariant)."
  - "Test: two critique calls with lens_first=True, identical lens_content, DIFFERENT system_prompt emit a byte-identical first system block (the duo synth/challenger shared-cache invariant)."
  - "Both new params are keyword-only and additive; every existing test in test_parallel.py and test_critic.py passes unchanged."
  - "pytest collected-test count strictly increases; ruff + ruff-format clean; pyright strict clean."
  - "docs/CURRENT_STATE.md updated; minor version bump in pyproject.toml (additive public-API change). NOTE: repo has no CHANGELOG.md — the changelog convention here is CURRENT_STATE.md + version bump + commit message."
files:
  touched:
    - src/spec_agents/agents/parallel.py
    - src/spec_agents/agents/critic.py
    - tests/test_parallel.py
    - tests/test_critic.py
    - docs/CURRENT_STATE.md
    - pyproject.toml
    - .agent/tasks/code-review-swarm.md
  must-not-touch:
    - src/spec_agents/caching.py          # reuse cached_text_block as-is; do not alter
    - src/spec_agents/usage.py            # single-source pricing untouched
    - src/spec_agents/eval/               # unrelated band
    # Invariant (not a path): within parallel.py the MapResult/MapUsage dataclass
    # shapes and the default-path (cached_prefix_text=None) system payload must not change.
---

# code-review-swarm: corpus-first cache prefix (sprint A — spec_agents foundation)

## Why
The code-review-swarm tool (design: `planning/architecture-reviews/2026-06-01-code-review-swarm-design.md`,
rev. 3) runs ~120 Haiku agents/pass plus Sonnet and Opus tiers over **one whole-repo corpus**. To make
that affordable the corpus must be created in the cache **once for the entire run** and read by every
subsequent call across all tiers. Today the corpus can only sit in `map_agent`'s single cached block (so
it re-creates whenever the per-tier preamble changes) and in `critique`'s lens block *after* the rules (so
the synthesizer and challenger, which have different rules, each create their own copy). This sprint adds
the two small, additive primitive hooks that let a caller put the corpus in a stable **leading** cached
block — the foundation sprint B (the planning script) depends on.

## What
Two additive, keyword-only, backward-compatible changes. No behavior change on the default paths.

**1. `map_agent(..., cached_prefix_text: str | None = None)`** in `src/spec_agents/agents/parallel.py`.
Today: `system = [cached_text_block(shared_system_text)]`. Change to:
```python
if cached_prefix_text is None:
    system = [cached_text_block(shared_system_text)]  # unchanged default
else:
    system = [
        cached_text_block(cached_prefix_text),  # stable corpus, the ONLY cached block
        {"type": "text", "text": shared_system_text},  # per-tier preamble, uncached, varies
    ]
```
Anthropic caches the prefix up to the breakpoint, so the corpus block hits regardless of the trailing
preamble — one create, reused across passes and tiers.

**2. `critique(..., lens_first: bool = False)`** in `src/spec_agents/agents/critic.py`.
Today: `system_blocks = [rules, (cached) lens]`. When `lens_first=True` and `lens_content` is set, build
`[(cached) lens, rules]` instead, so two roles with different `system_prompt` (rules) share one cached
lens block. Keep the cache_control / `cache_lenses` semantics identical; only the order flips.

Tests (stub `client.messages.create` capturing kwargs — mirror the existing fakes in test_parallel.py /
test_critic.py; no live API): assert block ordering, cache_control placement, the two cross-call
byte-identity invariants, and that omitting the params reproduces today's exact `system` payload.

## Out of scope
- The consumer script `code_review_swarm.py` — that is **sprint B**, in the `planning` repo. Not here.
- Any new `map_agent`/`critique` features beyond these two kwargs (no multi-breakpoint, no TTL handling,
  no batching helpers — sprint B does batching at the call site).
- Changing `MapResult`/`MapUsage`, `warm_then_fan_out`, `cached_text_block`, or pricing.
- Reviewer lenses, slicing logic, report rendering — all sprint B.

## Notes
- `cached_text_block` (caching.py:50) already emits `{"type":"text","text":…,"cache_control":{"type":"ephemeral"}}`
  — reuse it for the leading block; the trailing preamble is a plain text block (no helper).
- `lens_first=False` is the default precisely so every existing `critique` caller (spectacular's audit DAG,
  deep_review) is byte-for-byte unaffected.
- New-feature lens: every new code path gets a test; bump version + CHANGELOG since the public signatures
  grow; update CURRENT_STATE.
- Verification doc must list each new test by name, state the system-block invariants proven, and confirm
  the default-path payloads are unchanged.

## References
- `planning/architecture-reviews/2026-06-01-code-review-swarm-design.md` (rev. 3) — §1 Caching, "What this
  requires (small spec_agents change)".
- `src/spec_agents/agents/parallel.py` `map_agent` (system build ~line 108).
- `src/spec_agents/agents/critic.py` `critique` (system_blocks build ~line 94).
- Sprint B (follow-on): `planning/scripts/code_review_swarm.py`.
