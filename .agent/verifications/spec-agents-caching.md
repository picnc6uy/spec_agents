---
task-id: spec-agents-caching
verified: 2026-05-29
status: ready-to-merge
agent: claude-code
---

# Verification for spec-agents-caching

New kernel module `spec_agents.caching` (token-wise prompt-cache helpers).
**Kernel-freeze exception, operator-granted 2026-05-29** (mirrors the usage-cost-fn exception).
Verified with `C:/Users/ghendrick/AppData/Local/Programs/Python/Python312/python.exe`.

## Automated checks
- [x] `pytest -q` — **88 passed** (full suite; +15 new in tests/test_caching.py). No regressions.
- [x] `ruff check` (caching.py + test) — All checks passed.
- [x] `ruff format --check` — 2 files already formatted.
- [x] `pyright src/spec_agents/caching.py` — **0 errors, 0 warnings** (strict-clean; module is in the include surface).

## Acceptance criteria
- [x] `src/spec_agents/caching.py` exports `cached_text_block`, `warm_then_fan_out`, `is_cache_churning` (`__all__` set).
- [x] Library-mode: no Anthropic client, no API calls, no I/O. `run` is caller-supplied. Mirrors usage.py posture.
- [x] `warm_then_fan_out`: empty→[]; single→[run(t0)]; order preserved (test with out-of-order completion);
  warm=True completes tasks[0] before any fan-out task starts (deterministic `threading.Event` test:
  `test_warm_true_completes_first_task_before_any_fanout_starts`, zero violations); warm=False fans all;
  exceptions propagate (incl. a warm-up failure aborting before fan-out).
- [x] `cached_text_block` returns `{'type':'text','text':...,'cache_control':{'type':'ephemeral'}}` with a
  FRESH cache_control dict per call (`test_..._returns_fresh_cache_control_each_call` proves no aliasing).
- [x] 15 tests in tests/test_caching.py covering all of the above incl. churn heuristic (no-creation→False,
  zero-reads→True, creation-dwarfs-reads→True, healthy→False, configurable threshold).
- [x] `__init__.py` submodule docstring lists `caching`; version 0.8.0→0.9.0 in __init__.py + pyproject.toml.
- [x] Full suite green; ruff + pyright clean.

## Out-of-scope confirmation
- [x] No consumer edited (spectacular reviewers / critic to be wired in the next sprint).
- [x] `warm_then_fan_out` stays model-agnostic — no Anthropic call inside; caller's `run` owns the API + usage recording.
- [x] No 1-hour TTL param (documented follow-up); no UsageTracker lift; no tag/push/pin-bump (operator release step).
- [x] must-not-touch held: usage.py / agents/ / eval/ / storage/ / ingestion/ unchanged. `git diff --name-only`
  = caching.py (new), __init__.py, pyproject.toml, tests/test_caching.py (new), .agent/.

## Things I deliberately did not do
- Did not add a `ttl="1h"` extended-cache option — ephemeral only; flagged as a follow-up param when a consumer needs it.
- Did not wire the helper into any consumer — that's the spectacular audit-DAG fix sprint (next).
- Did not tag v0.9.0 or bump consumer pins — operator-initiated release.

## Risks for human reviewer
- `warm_then_fan_out` relies on `run` being thread-safe w.r.t. closed-over state. Documented; the Anthropic
  SDK client is safe for concurrent `messages.create`. The kernel can't enforce caller thread-safety.
- The warm-before-fan-out *ordering* guarantee is what yields "1 create + N-1 reads" in production; the test
  proves the ordering deterministically without real API calls (the cache behavior itself is Anthropic's).

## Diff summary
- 2 new files (caching.py ~150 lines, test_caching.py 15 tests) + 2 one-line version bumps + 1 docstring line.

## Verdict
Ready to merge.
