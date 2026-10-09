---
task-id: sa-prices-55-1
verified: 2026-10-09
status: ready-to-merge
agent: claude-code
---

# Verification for sa-prices-55-1

Interpreter for every gate: `C:\Users\ghendrick\AppData\Local\Programs\Python\Python312\python.exe` (3.12). No SKIP=.

## Automated checks
- [x] `pytest -q` per file (full suite left to the merge gate): test_usage.py 29 passed; test_parallel.py 13 passed; test_budget.py 32 passed (budget unmodified).
- [x] `pyright` -- 0 errors, 1 pre-existing warning (psutil import in budget.py).
- [x] `ruff check .` -- All checks passed; `ruff format --check src tests` -- 48 files unchanged.
- [x] `git diff --name-only origin/master...HEAD` is a subset of files.touched (spec, CURRENT_STATE, usage.py, parallel.py, test_usage.py, test_parallel.py, this doc). test_budget.py not needed.

Test counts (static `def test_`): test_usage.py 11 -> 26 defs (29 collected with parametrize); test_parallel.py 11 -> 13. Pre-commit hooks (detect-secrets, agent-task discipline, drift-audit) passed on commit.

## Acceptance criteria
- [x] P1 rates -- `test_{opus,sonnet,haiku}_5_5_mixed_call_by_hand` assert equality to 1e-12 against hand-computed values.
- [x] P2 cache read flat -- `test_5_5_cache_read_is_flat_not_point_one_x_input`; row comments say so.
- [x] P3 citation -- each row cites platform.claude.com/docs/en/about-claude/pricing, read 2026-10-09; module docstring and table comment no longer imply the 2026-05-30 date covers them.
  **Page re-read: NOT performed.** This session has no web-fetch tool, so I could not re-read the page; I used the spec author's rates (cross-checked in the spec Notes against the 2026-10-07 brief). No rate difference observed because no independent read happened. The reviewer/driver should confirm the rates against the page.
- [x] P4 Haiku 5.5 long prompt -- tests: `test_haiku_5_5_threshold_boundary` (100,000 base / 100,001 long), `..._long_prompt_all_token_kinds_at_long_rates`, `..._cache_reads_count_toward_threshold`, `..._cache_creation_counts_toward_threshold`, `..._output_does_not_count_toward_threshold`, `test_5_5_big_models_have_no_threshold[opus/sonnet]`.
- [x] P5 per-request -- `map_agent` sums `model_cost_usd` per call (`math.fsum`); tests `test_map_agent_haiku_5_5_prices_each_call_at_base_rate_when_sum_is_over_threshold`, `..._long_rate_applies_only_to_the_long_call`. MapUsage totals unchanged.
- [x] P6 nothing else moves -- `test_pre_existing_rows_unchanged` (literal values per key), `test_unknown_or_dated_5_5_id_raises_keyerror` (gpt-4o, claude-haiku-5-5-20260101, claude-opus-5-5-20260101); keyword names unchanged; existing tests pass unmodified.
- [x] P7 -- module still pure; DEFAULT_PARALLEL_MODEL untouched.

## Out-of-scope confirmation
- [x] No must-not-touch item modified (no existing row values, pyproject, planning, settings).

## Things I deliberately did not do
Nothing beyond the spec: no default-model switch, no 1h cache / batch / fast mode.

## Spec interpretation notes
Long-prompt rates stored in two new module tables (`LONG_PROMPT_THRESHOLD_TOKENS`, `LONG_PROMPT_PRICING_USD_PER_MTOK`), as the spec left that to the builder. The "no changes/ note" is met by CURRENT_STATE.md.

## Self-review
`/code-review high` on a detached copy of `origin/master...HEAD`. Findings and disposition:
- Missing verification doc -- fixed (this doc).
- `sum()` returns int 0 for empty fan-out / order-dependent float sum -- fixed (`math.fsum`).
- Two parallel dicts could drift -- fixed with `test_threshold_and_long_tables_have_same_models`; not merged into one structure (kept as small, tested).
- Totals can't be re-priced to match `cost_usd` -- fixed in `map_agent` docstring.
- No cache_creation threshold test -- fixed (added).
- Structural four-key test for new rows -- fixed (added).
- Stale "spec drafted" CURRENT_STATE section -- fixed (removed). Generated test-count facts block is machine-written; left alone.
- Rates unverified against second source -- not fixable here (no network tool); flagged under P3 and Risks.

## Risks for human reviewer
1. 5.5 rates were not re-read from the pricing page by me; confirm them.
2. Anything re-pricing `MapUsage` totals with `model_cost_usd` would over-bill Haiku 5.5.

## Documentation drift (per the drift-audit lens)
- [x] `docs/CURRENT_STATE.md` updated with the pricing entry.
- [x] No planning cross-repo status lines affected.
- [x] No memory entries affected.
- [x] Path references unchanged.

## Diff summary
- 7 files vs origin/master (incl. spec); usage.py +table/threshold logic, parallel.py per-call pricing, tests +17 defs.

## Verdict
Ready to merge, pending a human/driver confirmation of the 5.5 rates against the pricing page (not re-read by the builder).
