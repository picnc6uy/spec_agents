---
id: usage-cost-fn
title: Add spec_agents.usage.model_cost_usd — single-source pricing function
type: new-feature
lens: new-feature
created: 2026-05-28
status: drafted
acceptance:
  - "spec_agents.usage exports model_cost_usd(model, input_tokens, output_tokens, *, cache_creation_tokens=0, cache_read_tokens=0) -> float"
  - "spec_agents.usage exports PRICING_USD_PER_MTOK as the single source of truth (Opus 4.8/4.7, Sonnet 4.6, Haiku 4.5)"
  - "Unknown model raises KeyError (explicit, catchable) — tested failure path"
  - "Cost formula matches spectacular/scripts/_usage_tracker.py (input + output + cache_creation + cache_read, per MTok)"
  - "New tests cover: known-model cost, cache-token cost, zero tokens, unknown-model KeyError"
  - "pytest -q green; ruff + ruff-format clean"
  - "version bumped 0.7.0 -> 0.8.0 (pyproject + __init__); CURRENT_STATE public-surface + Tag refreshed"
files:
  touched:
    - src/spec_agents/usage.py
    - tests/test_usage.py
    - src/spec_agents/__init__.py
    - pyproject.toml
    - docs/CURRENT_STATE.md
    - .agent/tasks/usage-cost-fn.md
    - .agent/verifications/usage-cost-fn.md
  must-not-touch:
    - src/spec_agents/agents/
    - src/spec_agents/eval/
    - src/spec_agents/storage/
    - src/spec_agents/knowledge/
    - src/spec_agents/ingestion/
    - src/spec_agents/messages.py
    - src/spec_agents/logging.py
    - src/spec_agents/testing/
---

# usage-cost-fn: Add spec_agents.usage.model_cost_usd — single-source pricing function

## Why
The token→USD cost formula and the per-model price table are duplicated across ≥5 sites
(spectacular `_usage_tracker.py`, `synthesizer.py`, `weekly_auditor.py`; personal_os
`action_extractor.py`, `daily_brief.py`). The Opus 4.7→4.8 pricing change already caused a
memo to ship with stale prices because a copy was missed. The comprehensive review
(`planning/architecture-reviews/2026-05-28-comprehensive-review-synthesis.md`, Open Q3)
recommended a single kernel home for *the one thing that changes*. Operator granted a
kernel-freeze exception for this small pure function (not the full UsageTracker).

## What
Add `src/spec_agents/usage.py` exporting:
- `PRICING_USD_PER_MTOK: dict[str, dict[str, float]]` — public pricing table (input, output,
  cache_creation, cache_read per MTok) for claude-opus-4-8, claude-opus-4-7,
  claude-sonnet-4-6, claude-haiku-4-5-20251001. Lifted verbatim from `_usage_tracker.py`.
- `model_cost_usd(model, input_tokens, output_tokens, *, cache_creation_tokens=0,
  cache_read_tokens=0) -> float` — pure function, no side effects. Computes
  `(in*price_in + out*price_out + cc*price_cc + cr*price_cr) / 1_000_000`. Raises `KeyError`
  for an unknown model (explicit; the lenient "record unknown at $0" behavior stays in the
  caller, e.g. UsageTracker can catch KeyError → 0.0).

This is purely additive — no existing module changes, no consumer is forced to adopt it.
spectacular's `_usage_tracker.py` and personal_os inline formulas can migrate to it in
later sprints (`spec-inrepo-utils` / personal_os hygiene), out of scope here.

## Out of scope
- Lifting the full `UsageTracker` class / `wrap_anthropic_module` (single consumer; thread-
  safety wrinkle; waits per synthesis memo).
- Migrating any existing consumer to call the new function.
- Tagging/pushing v0.8.0 (done on master post-close, not on the branch).

## Notes
Cache multipliers per Anthropic docs: cache_creation ≈ 1.25× input, cache_read ≈ 0.1× input
(already baked into the lifted table). KeyError-on-unknown is the deliberate semantic choice
(a new function gets clean semantics; silent $0 is a footgun).

## References
- planning/architecture-reviews/2026-05-28-comprehensive-review-synthesis.md (Open Q3 + Extraction "Lift to kernel")
- spectacular/scripts/_usage_tracker.py (source of the pricing table + formula)
