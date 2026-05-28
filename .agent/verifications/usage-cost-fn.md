---
task-id: usage-cost-fn
verified: 2026-05-28
status: ready-to-merge
agent: claude-code
---

# Verification for usage-cost-fn

## Automated checks
- [x] `pytest -q` — **73 passed in 1.52s** (was 67; +6 new tests in test_usage.py)
- [x] `pyright --pythonpath <Py312>` — **0 errors, 0 warnings** (v1.1.360, matches CI pin). Bare-worktree `pyright` without `--pythonpath` shows 18 pre-existing reportMissingImports for third-party deps (sqlalchemy/anthropic) — environment noise, not code; CI installs `.[dev]` so it sees 0. usage.py imports only `typing`.
- [x] `ruff check .` — All checks passed
- [x] `ruff format --check .` — 35 files already formatted
- [x] `git diff --name-only main..HEAD` matches files.touched (see Diff summary)

## Acceptance criteria
- [x] `spec_agents.usage` exports `model_cost_usd(model, input_tokens, output_tokens, *, cache_creation_tokens=0, cache_read_tokens=0) -> float`
  Evidence: src/spec_agents/usage.py:58-87; keyword-only cache params; pure function.
- [x] exports `PRICING_USD_PER_MTOK` as single source of truth (Opus 4.8/4.7, Sonnet 4.6, Haiku 4.5)
  Evidence: usage.py:28-55; test_pricing_table_has_all_current_tiers asserts the four cost keys per tier.
- [x] Unknown model raises KeyError (tested failure path)
  Evidence: usage.py:80 `PRICING_USD_PER_MTOK[model]`; test_unknown_model_raises_keyerror (pytest.raises(KeyError)).
- [x] Cost formula matches spectacular/scripts/_usage_tracker.py
  Evidence: identical `(in*input + out*output + cc*cache_creation + cr*cache_read) / 1_000_000`; cross-checked _usage_tracker.py:96-101.
- [x] New tests cover known-model, cache-token, zero-token, unknown-model paths
  Evidence: test_usage.py — 6 tests: known cost (Opus $30/2MTok), Sonnet differs ($18), cache priced ($6.75), zero=0.0, KeyError, table completeness.
- [x] pytest green; ruff + ruff-format clean — see Automated checks.
- [x] version bumped 0.7.0 → 0.8.0 (pyproject:7 + __init__.py:20); CURRENT_STATE Tag + public-surface + test count + resume step refreshed.

## Out-of-scope confirmation
- [x] No files in must-not-touch were modified.
  Evidence: diff touches only usage.py (new), test_usage.py (new), __init__.py, pyproject.toml, docs/CURRENT_STATE.md, .agent/{tasks,verifications}/usage-cost-fn.md. No agents/ eval/ storage/ knowledge/ ingestion/ messages.py logging.py testing/ changes.

## Things I deliberately did not do
- Did NOT lift the full UsageTracker / wrap_anthropic_module (single consumer; thread-safety wrinkle; deferred per synthesis memo).
- Did NOT migrate any existing consumer (spectacular _usage_tracker.py, personal_os inline formulas) to call the new function — those are later sprints.
- Did NOT tag/push v0.8.0 from the branch — tag is applied on master after ff-merge.

## Risks for human reviewer
- KeyError-on-unknown-model is a deliberate semantic choice and differs from UsageTracker's "record unknown at $0". When UsageTracker later adopts this fn, it must wrap the call in try/except KeyError to preserve its lenient behavior. (Documented in usage.py docstring.)
- PRICING_USD_PER_MTOK is now duplicated between kernel and spectacular/_usage_tracker.py until the consumer migration sprint — intentional (additive-only), but the two tables must not drift in the interim. Migration sprint should delete the _usage_tracker.py copy.

## Documentation drift (per the drift-audit lens)
- [x] docs/CURRENT_STATE.md updated (Tag v0.8.0, public surface += usage, tests 67→73, resume step). Master-commit SHA line uses the commit subject; exact SHA refreshed in the cross-repo drift pass at end of run.
- [x] Cross-repo: planning/HANDOVER.md will note v0.8.0 in the run's closing HANDOVER refresh.
- [x] Memory: reference_model_tiers holds canonical pricing; the new kernel table cites it. No memory edit needed.
- [x] Path references resolve (usage.py cites _usage_tracker.py + synthesis memo, both present).

## Diff summary
- 7 files changed: +usage.py (88), +test_usage.py (54), __init__.py (+1 doc line, version), pyproject.toml (version), CURRENT_STATE.md (Tag/surface/tests/resume), task spec, verification doc.
- New public symbol: `spec_agents.usage.model_cost_usd` + `PRICING_USD_PER_MTOK`. Version 0.7.0 → 0.8.0.

## Verdict
Ready to merge. Purely additive kernel function (operator-approved freeze exception); 6 new tests; all gates green; no consumer forced to change.
