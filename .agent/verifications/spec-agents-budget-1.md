---
task-id: spec-agents-budget-1
verified: 2026-10-02
status: ready-to-merge
agent: claude-code
---

# Verification for spec-agents-budget-1

Interpreter for every gate: `C:\Users\ghendrick\AppData\Local\Programs\Python\Python312\python.exe`, `PYTHONPATH=src`, commit 7bb8ccc. No `SKIP=`; the pre-commit hooks passed on both commits.

## Automated checks
- [x] `pytest -q` -- `172 passed in 4.05s` (baseline 140 on master; +32 in tests/test_budget.py; test_caching.py and test_parallel.py unedited)
- [x] `pyright --pythonpath <interpreter>` -- `0 errors, 0 warnings, 0 informations`
- [x] `ruff check .` -- `All checks passed!`; `ruff format --check .` -- `93 files already formatted`
- [x] `git diff --name-only origin/master..HEAD`:
  ```
  .agent/tasks/spec-agents-budget-1.md   (spec commit)
  AGENTS.md
  docs/CURRENT_STATE.md                  (spec commit's `## As of`)
  src/spec_agents/__init__.py
  src/spec_agents/agents/parallel.py
  src/spec_agents/budget.py
  src/spec_agents/caching.py
  tests/test_budget.py
  ```
  All are in `files.touched`. The verification doc is the ninth.

## Acceptance criteria
- [x] P1 workers(). Evidence: `tests/test_budget.py` `test_workers_cap_and_floor[12-8|5-1|1-1|None-1]`, `..._argument_beats_variable`, `..._variable_beats_cap`, `..._blank_variable_ignored`, `..._bad_variable_raises[0|-1|abc]`, `..._bad_argument_raises[0|-1]`, plus bool/float rejection. Mutation runs, each restored afterwards:
  - drop `- 4`: 3 failed (`cap_and_floor[12-8]`, `[5-1]`, `blank_variable_ignored`)
  - drop None branch: 1 failed (`cap_and_floor[None-1]`)
  - drop env read: 6 failed (`variable_beats_cap`, `bad_variable_raises` x3, both pool-default tests)
  - Master has no `spec_agents.budget`, so these tests cannot import there.
- [x] P2 below_normal(). Evidence: in-process tests cover the POSIX, Windows-psutil, Windows-ctypes and unknown-platform branches (`test_posix_*`, `test_windows_psutil_*`, `test_windows_ctypes_*`, `test_unknown_platform_returns_false`), all with fakes, so the pytest process's priority never changes. `test_below_normal_real_process_twice` runs a real child (`sys.executable`, timeout 60 s): both calls True, equal readings, 0x4000 on Windows. Mutations:
  - drop POSIX at-or-below: 1 failed (`test_posix_never_moves_upward`)
  - narrow the exception guard: 2 failed (`posix_refusal`, `windows_psutil_refusal`)
  - The Windows at-or-below check is covered by `test_windows_psutil_never_moves_upward` and `test_windows_ctypes_never_moves_upward`; I did not run a mutation for it (the first mutation attempt had a PowerShell error and I moved on).
  - **Divergence from the spec's mutation claim:** the subprocess "twice" test does not catch removal of the at-or-below check on Windows. A second `SetPriorityClass(0x4000)` is a no-op, so both readings still match. The fake-backed tests catch it.
- [x] P3 pool defaults. Evidence: `test_warm_then_fan_out_default_uses_budget`, `test_map_agent_default_uses_budget` (`SPEC_AGENTS_WORKERS=2` set after import, 5 tasks, warm=False, pool recorded as `[2]`) and the `_explicit_wins` pair (`[4]`). Both signatures now read `max_workers: int | None = None`.

## Round 2 (R2-1, R2-2)
Interpreter: `C:\Users\ghendrick\AppData\Local\Programs\Python\Python312\python.exe`, `PYTHONPATH=src`, commit 574d56b. No `SKIP=`; pre-commit hooks passed.
- R2-1: `budget._below_normal_windows` returns False behind an `if sys.platform != "win32"` guard before `ctypes.windll`, which narrows it for pyright on every platform. Refusal paths still return False without raising.
  ```
  pyright --pythonpath <interpreter> --pythonplatform Linux   -> 0 errors, 0 warnings, 0 informations
  pyright --pythonpath <interpreter> --pythonplatform Windows -> 0 errors, 0 warnings, 0 informations
  ruff check .            -> All checks passed!
  ruff format --check .   -> 94 files already formatted
  pytest -q               -> 172 passed in 5.12s
  ```
- R2-2: `docs/CURRENT_STATE.md` `## As of 2026-10-02` now reads "spec-agents-budget-1 shipped" and describes `spec_agents.budget`, `SPEC_AGENTS_WORKERS` and the two defaults.
- Round-2 self-review (`/code-review high`, detached copy `$env:TEMP\review-spec-agents-budget-1`, removed; `origin/master...HEAD`). Nothing fixed; all left, with reasons:
  - cpu_count-4 default too low for network-bound pools / ignores affinity: the spec's P1 verbatim (already raised to the driver).
  - workers() resolved before `if pending`, so a bad env var raises even with no pool: deliberate round-1 fix (fail before a paid warm call).
  - Explicit `max_workers` not validated (0 clamps to 1): the spec requires today's behavior for explicit callers.
  - os.nice is per-thread on Linux; psutil/ctypes duplication; broad int() parsing (`1_0`, `+3`): the parse is a listed follow-up; the rest is out of scope.
  - Child PYTHONPATH overwrite in the real-process test; caching->budget import coupling: minor, left.

## Out-of-scope confirmation
- [x] No files in `files.must-not-touch` were modified. Evidence: the diff list above has no pyproject.toml, ci.yml, tests/test_caching.py, tests/test_parallel.py or scripts/bump_consumers.py. `__version__` stays 0.12.0 and the repo-facts block is untouched.

## Things I deliberately did not do
- No version bump and no changelog (the repo has none; the spec cuts it).
- Nothing in `spec_agents` calls `below_normal()`.

## Spec interpretation notes
- Windows ctypes path uses `ctypes.c_void_p(-1)` as the current-process pseudo-handle instead of `GetCurrentProcess()`. A bare Python int is passed as a 32-bit C int, and the real-process test measured `0x0` with it.
- `workers()` also rejects bool and float arguments with ValueError (a review finding).
- The P1 QUESTION default applies (raise on bad values); I did not ask the driver.
- The task file's frontmatter reads `status: drafted`, not the `draft` the prompt names. I left it; this doc's line is the one set.

## Self-review
`/code-review high` on a detached worktree (`$env:TEMP\review-spec-agents-budget-1`, since removed), covering `origin/master...HEAD` at 98b2ac6. Eight findings.

Fixed (commit 7bb8ccc):
- `budget.workers()` ran after the warm call, so a bad `SPEC_AGENTS_WORKERS` raised after a paid call. It now resolves first (`test_bad_variable_fails_before_warm_call`).
- `_parse_workers` accepted bool and float and missed OverflowError. Fixed (`test_workers_rejects_bool_and_float`).
- The real-process test would fail under an IDLE parent. It now accepts 0x40 or 0x4000.
- Duplicated at-or-below rank logic. Replaced with the `_WIN_AT_OR_BELOW` frozenset.

Left, with reason:
- Default `cpu_count - 4` drops a 4-core box from 6 to 1 worker and a 64-core box to 60. This is the spec's P1 property verbatim (operator-approved). Driver should confirm it is intended for network-bound pools.
- POSIX platform allowlist misses cygwin/aix/sunos. The spec requires unknown platforms to return False, and `hasattr(os, "nice")` would break that test on Linux. Left.
- `docs/CURRENT_STATE.md` `## As of` says "Task spec only". It came from the spec commit and the spec permits only a new `## As of` section there. Driver may add a newer one at merge.
- Missing verification doc: this document.

## Risks for human reviewer
- Behaviour change for every consumer that does not pass `max_workers`: the default pool is now machine-derived (1 on <=5 cores, uncapped above), no longer 6. Rate limits on big boxes are the exposure; consumers can set `SPEC_AGENTS_WORKERS`.
- The psutil path was exercised only with fakes in-process plus the real child, and psutil is installed in this box's Python312. The ctypes fallback is covered by fakes only (the real-read in the child used ctypes, but the set path ran through psutil).

## Documentation drift (per the drift-audit lens)
- [x] `docs/CURRENT_STATE.md` `## As of 2026-10-02` now says what shipped (R2-2).
- [x] No cross-repo claims affected.
- [x] No memory entries affected.
- [x] Path references unchanged.

## Diff summary
- 8 files changed vs origin/master, about +520 / -6 lines. New: `src/spec_agents/budget.py`, `tests/test_budget.py` (32 tests). Changed: the two `max_workers` defaults and docstrings, the `__init__` Submodules line, the AGENTS.md surface list.

## Verdict
Ready to merge.
