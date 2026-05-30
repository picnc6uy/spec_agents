---
task-id: spec-agents-parallel
verified: 2026-05-30
status: ready-to-merge
agent: claude-code
---

# Verification for spec-agents-parallel

New `spec_agents.agents.parallel.map_agent` — Haiku-parallel item processing over a warmed
shared cache. **Kernel-freeze exception — extension of the operator-sequenced caching→parallelism
initiative.** Verified with `C:/Users/ghendrick/AppData/Local/Programs/Python/Python312/python.exe`.

## Automated checks
- [x] `pytest -q` (full suite) — **96 passed** (+8 new in tests/test_parallel.py). No regressions.
- [x] `ruff check` (parallel.py + test) — All checks passed.
- [x] `ruff format --check` — 2 files already formatted (test auto-formatted during the run).
- [x] `pyright src/spec_agents/agents/parallel.py` — **0 errors, 0 warnings** (strict-clean; in the include).

## Acceptance criteria
- [x] `parallel.py` exports `map_agent`, `MapResult`, `MapUsage`, `DEFAULT_PARALLEL_MODEL` (`__all__` set).
- [x] map_agent builds a cached system block from `shared_system_text` (cache_control ephemeral),
  per-item content via `build_user_content` in the user turn, runs via `warm_then_fan_out(warm=True)`,
  parses each response, returns results in item order. Tests:
  `test_map_agent_returns_results_in_item_order`, `test_shared_system_is_cached_block_and_not_duplicated_per_item`.
- [x] Default model = `claude-haiku-4-5-20251001`, overridable (`test_default_model_is_haiku_and_overridable`).
- [x] tools/tool_choice forwarded only when provided (`test_tools_and_tool_choice_passthrough_only_when_provided`).
- [x] Usage aggregated from response.usage (getattr-safe); MapUsage has totals + cost_usd
  (model_cost_usd) + churning (is_cache_churning). Tests: `test_usage_aggregates_across_the_fanout`
  (exact Haiku-rate cost arithmetic), `test_churning_flag_set_when_creation_dwarfs_reads`.
- [x] Library-mode: caller owns client + per-item prompt + parse; map_agent owns only the
  cache-correct fan-out + rollup. Mirrors critic.py. No framework added.
- [x] warm-then-fanout re-asserted at this layer (`test_warm_completes_before_fanout_starts`,
  threading.Event, zero violations). Empty items → []/zero usage (`test_map_agent_empty_items`).
- [x] agents/__init__ + spec_agents/__init__ docstrings updated; version 0.9.0→0.10.0 (pyproject + __init__).
- [x] Full suite green; ruff + pyright clean.

## Out-of-scope confirmation
- [x] must-not-touch held: caching.py / usage.py / critic.py / eval/ unchanged (composed, not edited).
  `git diff --name-only` = parallel.py (new), agents/__init__.py, __init__.py, pyproject.toml,
  tests/test_parallel.py (new), .agent/.
- [x] No retry wrapper, no multi-model aggregation, no 1h TTL, no real-consumer wiring, no tag/pin-bump.

## Things I deliberately did not do
- Did not wire a real consumer (photo_archive parser, etc.) — the massive-processing workload is an
  operator choice; offered separately.
- Did not tag v0.10.0 / bump consumer pins — operator release step (though v0.9.0 was tagged this
  session for the audit fix; v0.10.0 tag is offered).
- Single-model cost assumption (one `model` per map) — the massive-processing case; documented.

## Risks for human reviewer
- `map_agent` makes the API call (agents band, like critic) — slightly less pure than the
  caching primitives, but consistent with the charter's agents-band precedent (a callable, not a framework).
- The Haiku default is a cost/quality choice; callers override `model` for harder tasks. The cost rollup
  + churning flag make a large run's spend and cache-effectiveness observable.

## Diff summary
- 2 new files (parallel.py ~170 lines, test_parallel.py 8 tests) + 2 docstring updates + 2 version bumps.

## Verdict
Ready to merge.
