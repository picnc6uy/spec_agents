---
id: spec-agents-parallel
title: spec_agents.agents.parallel.map_agent — Haiku-parallel item processing with a warmed shared cache
type: new-feature
lens: new-feature
created: 2026-05-30
status: drafted
budget:
  max_iterations: 40
  max_cost_usd: 4.00
  on_breach: abort-to-needs-rework
acceptance:
  - "NEW `src/spec_agents/agents/parallel.py` exports `map_agent(...)` (library-mode agent-band callable) + `MapResult` + `MapUsage` dataclasses."
  - "map_agent fans a per-item model call over `items`: builds a cached system block from `shared_system_text` (via spec_agents.caching.cached_text_block), per-item variable content via `build_user_content(item)` in the user turn, runs via `warm_then_fan_out(warm=True)` so item[0] warms the shared cache and the rest cache-read; parses each response via `parse(response)`; returns results in item order."
  - "Default model is `claude-haiku-4-5-20251001` (the massive-processing workhorse); overridable. tools/tool_choice passed through only when provided."
  - "Usage aggregated across the fan-out from response.usage (input/output/cache_creation_input/cache_read_input tokens, getattr-safe); MapUsage carries totals + cost_usd (via spec_agents.usage.model_cost_usd) + churning (via spec_agents.caching.is_cache_churning)."
  - "Library-mode: the caller owns the client + the per-item prompt + the parse; map_agent owns only the cache-correct fan-out + usage rollup. Matches critic.py's posture (agents band makes the call)."
  - "tests/test_parallel.py (fake client, NO real API): results in item order; shared_system_text is in a cached system block and NOT duplicated per item; build_user_content drives the user turn; default Haiku model; usage aggregation correct; churning flag reflects cc-vs-cr; warm-then-fanout ordering (item[0] completes before the rest, threading.Event); tools/tool_choice passthrough. >=9 cases, all pass."
  - "agents/__init__ docstring + spec_agents/__init__ submodule list updated; version 0.9.0 -> 0.10.0 (pyproject + __init__). Kernel-freeze EXCEPTION — extension of the operator-sequenced caching→parallelism initiative (2026-05-30), recorded in Why."
  - "Full suite green; ruff + ruff format clean; pyright strict-clean on the new module."
files:
  touched:
    - src/spec_agents/agents/parallel.py     # NEW
    - src/spec_agents/agents/__init__.py      # docstring: add parallel primitive
    - src/spec_agents/__init__.py             # submodule note + __version__ 0.10.0
    - pyproject.toml                           # version 0.9.0 -> 0.10.0
    - tests/test_parallel.py                  # NEW
    - .agent/tasks/spec-agents-parallel.md
    - .agent/verifications/spec-agents-parallel.md
  must-not-touch:
    - src/spec_agents/caching.py              # consume; do not edit
    - src/spec_agents/usage.py                # consume; do not edit
    - src/spec_agents/agents/critic.py
    - src/spec_agents/eval/
---

# spec-agents-parallel: Haiku-parallel item processing

## Why
**Kernel-freeze exception — extension of the operator-sequenced caching→parallelism initiative**
(2026-05-30; the caching half shipped as spec_agents.caching v0.9.0). The operator wants
"parallel agents running tasks in Haiku for massive processing and agent task specificity."

The orchestration substrate already exists (`warm_then_fan_out`). What massive processing still
needs is the **agent convenience** that wires the correct pattern in one call: a cached shared
instruction/context prefix (written once), a per-item specific prompt (the "agent task
specificity"), a Haiku call per item fanned out *after* the cache is warm, and a cost/usage
rollup so a 700-item run reports total spend + flags churn. `map_agent` is that callable — and
it inherits the cache-correctness from `warm_then_fan_out`, so massive parallel runs don't
re-trigger the cache-creation storm the caching work just fixed.

## What
NEW `src/spec_agents/agents/parallel.py` (library-mode, agents band — makes the call like critic):

`map_agent(*, client, items, shared_system_text, build_user_content, parse, model=HAIKU,
max_tokens=2048, tools=None, tool_choice=None, max_workers=6, warm=True) -> MapResult`:
- `system = [cached_text_block(shared_system_text)]` (stable prefix, cached, written once).
- per item: `messages=[{"role":"user","content": build_user_content(item)}]` (variable, uncached);
  add tools/tool_choice only if provided; `client.messages.create(**kwargs)`.
- record usage (getattr-safe: input_tokens / output_tokens / cache_creation_input_tokens /
  cache_read_input_tokens) under a lock; `parse(response) -> R`.
- run via `warm_then_fan_out(items, _run, max_workers, warm)` (item[0] warms; rest cache-read).
- aggregate → `MapUsage(calls, input, output, cache_creation, cache_read, cost_usd, churning)`
  where cost_usd = `model_cost_usd(model, ...)` and churning = `is_cache_churning(cc, cr)`.
- return `MapResult(results=<in item order>, usage=<MapUsage>)`.

Dataclasses `MapResult[R]` + `MapUsage` (frozen). Default model = Haiku.

## Out of scope
- A retry/backoff wrapper inside `_run` — caller's `parse`/client own that (compose with existing patterns).
- Multi-model cost aggregation (assumes one `model` for the map — the massive-processing case).
- 1-hour extended cache TTL — ephemeral only (warming handles the 5-min race).
- Wiring a real consumer (photo_archive parser, etc.) — that's a separate, operator-chosen workload.
- Tagging/pushing v0.10.0 or bumping consumer pins — operator release step.
- Editing caching.py / usage.py — compose them, don't modify.

## Notes
- New-feature lens: every new path tested. All tests use a fake client (canned response.content +
  response.usage) — zero API spend. The warm-before-fanout guarantee is re-asserted at this layer
  via threading.Event (item[0] sets it; later items assert it's set).
- Library-mode check: `map_agent` adds no framework — it's one function composing
  `cached_text_block` + `warm_then_fan_out` + `model_cost_usd` + `is_cache_churning`. The caller
  still owns the client, the per-item prompt, and the parse. Consistent with critic.py / the charter.
- pyright strict: type the generics (`items: Sequence[T]`, `parse: Callable[[Any], R]`,
  `MapResult[R]`); usage via getattr returns Any → coerce to int.

## References
- `spec_agents.caching` (v0.9.0) — warm_then_fan_out, cached_text_block, is_cache_churning
- `spec_agents.usage.model_cost_usd` — pricing
- `planning/standards/prompt-caching.md` — the rule this applies at scale
- `src/spec_agents/agents/critic.py` — agents-band precedent (the kernel agent that makes a call)
