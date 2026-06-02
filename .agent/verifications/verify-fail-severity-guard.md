---
task-id: verify-fail-severity-guard
verified: 2026-06-01
status: ready-to-merge
agent: claude-code
---

# Verification for verify-fail-severity-guard

`verify()` silently returned `passed=True` when `fail_severity` was a typo (the unknown threshold
ranked 99 via `_at_or_above`, so no real issue met it). Fix: validate `fail_severity` against
`_SEVERITY_RANK` at entry and raise `ValueError`. Found by the code_review_swarm dogfood review of
this repo (the one real [medium] bug among ~50 swarm filings).

Toolchain: worktree `.venv` (Python 3.12) with `pip install -e ".[dev]" ruff==0.8.4 pyright==1.1.360`.

## Automated checks
- [x] `pytest` (full) — **105 passed** (103 prior + **2 new**). No regressions.
- [x] `ruff check .` (pinned 0.8.4) — All checks passed.
- [x] `ruff format --check .` — 39 files already formatted.
- [x] `pyright` (pinned 1.1.360, strict, venv pythonpath) — **0 errors, 0 warnings**.
- [x] `git diff --name-only main..HEAD` ⊆ `files.touched`; `usage.py`/`parallel.py`/`critic.py` untouched.

## Bug-fix lens evidence (failing test first)
- **Fails on base** (fix stashed): both new tests fail —
  `FAILED test_verify_typoed_fail_severity_raises_not_silently_passes` and
  `test_verify_evidence_inherits_fail_severity_guard`. On base, `verify(rules=[emit_error],
  fail_severity="errrn")` returns `passed=True` with a real `error` issue present (no exception) →
  the assertion `pytest.raises(ValueError)` fails. This *is* the bug: a verification that cannot fail.
- **Passes after fix:** both green (`2 passed`). `verify()` raises
  `ValueError("unknown fail_severity 'errrn'; expected one of ['critical', 'error', 'info', 'warning'])`.
- **Nature:** longstanding (present since SA-003 shipped), not a regression — exposed by the swarm review.

## Acceptance criteria
- [x] **Reproduction test** present and was red-on-base, green-after — see above.
- [x] **`verify()` validates the threshold at entry** (raises `ValueError` naming the bad value + valid
  set). Signature unchanged (`*, rules, fail_severity="error"`).
- [x] **Known thresholds unchanged:** existing `test_verify_warning_*`, `test_verify_critical_*`,
  `test_result_passed_uses_severity_threshold_correctly` all still pass (default `"error"` + `"warning"`).
- [x] **Issue-severity asymmetry preserved:** `test_verify_unknown_severity_treated_as_failing` still
  passes — an unknown ISSUE severity ranks high and fails (only the THRESHOLD is validated).
- [x] **Wrappers inherit the guard:** `test_verify_evidence_inherits_fail_severity_guard` (verify_schema/
  verify_evidence forward `fail_severity` to `verify()`).
- [x] **Version bump 0.11.0 → 0.11.1; CURRENT_STATE updated.**

## Out-of-scope confirmation
- [x] `must-not-touch` held: `usage.py`, `parallel.py`, `critic.py` unchanged.
- [x] No signature change (would be a refactor). No issue-severity validation (the unknown-ranks-high
  default is the intended safe behavior there). Only `verifiers.py` + its test + version/docs touched.

## Things I deliberately did not do
- Did not make `fail_severity` a `Literal`/enum (a type-level fix) — that's a larger API change; the
  runtime guard is the smallest fix. Flagged as the preventative measure for the backlog.
- Did not tag v0.11.1 / bump consumer pins (operator release step).

## Risks for human reviewer
- Behavior change: callers that previously passed a typo'd `fail_severity` and got a (wrong) green now
  get a loud `ValueError`. That is the intended correction — but any caller relying on the broken
  silent-pass would now surface. Grep shows no such caller in-repo; consumers pass literals.

## Documentation drift (per the drift-audit lens)
- [x] `docs/CURRENT_STATE.md` updated (v0.11.1 landing entry).
- [x] Public surface (`verify`) signature unchanged; the new ValueError is documented in its docstring.
- Preventative recommendation (backlog): make `fail_severity` a `Literal["info","warning","error","critical"]`
  so a typo is a type error at the call site, not a runtime guard.

## Diff summary
- `verifiers.py`: +entry guard in `verify()` (+ docstring), tightened `_at_or_above` docstring. 2 new
  tests. Version 0.11.0 → 0.11.1. CURRENT_STATE entry.

## Verdict
Ready to merge.
