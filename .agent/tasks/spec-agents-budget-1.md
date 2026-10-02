---
id: spec-agents-budget-1
title: "spec_agents sizes its fan-out pools to the machine and can lower its own priority: a small budget module (workers, below_normal) replaces the hard-coded six workers in caching.py and agents/parallel.py"
type: new-feature
lens: new-feature
created: 2026-10-02
status: drafted
budget:
  # Soft caps the agent self-applies. On breach, do NOT grind on or fake green:
  # follow the escape-hatch contract in agent-task/RECOVERY.md.
  max_iterations: 80
  max_cost_usd: 8   # unit tests only; no live API call anywhere in this sprint
  on_breach: abort-to-needs-rework   # write needs-rework + reason; never silently continue
acceptance:
  - "P1 (the pool size fits the machine). Property: `spec_agents.budget.workers(explicit: int | None = None) -> int` returns `explicit` when given, else the integer in the environment variable `SPEC_AGENTS_WORKERS` when it is set and not blank, else `max(1, os.cpu_count() - 4)`, and 1 when `os.cpu_count()` returns None. Every input is read at call time, never at import. An explicit value (argument or variable) that is not an integer >= 1 raises ValueError naming its source (the QUESTION in Notes; this is its default). Test: tests/test_budget.py (new), with `os.cpu_count` monkeypatched: 12 -> 8, 5 -> 1, 1 -> 1, None -> 1 (the cap and its floor); the argument beats the variable; the variable beats the cap; a blank variable is ignored; `0`, `-1` and `abc` raise. Fails on master (no module); mutation-proven guard: dropping the `- 4`, the None branch or the variable read each fails a named test."
  - "P2 (the process can step aside). Property: `spec_agents.budget.below_normal() -> bool` leaves the current process at BELOW_NORMAL_PRIORITY_CLASS (0x4000) on Windows, through psutil when it imports and through ctypes kernel32 SetPriorityClass otherwise, and at a niceness of at least 10 on POSIX (os.nice), and returns True. It never moves a process that already runs at or below that level upward, so a second call changes nothing and returns True. A refused or failed OS call (an OSError, psutil's AccessDenied, SetPriorityClass returning 0, an unknown platform) returns False and never raises. Nothing inside spec_agents calls it; consumers opt in. Tests (tests/test_budget.py): (a) in-process, monkeypatching sys.platform and the OS call (`os.nice` with raising=False, a fake `psutil` or None in sys.modules, a fake `ctypes.windll`), so every branch runs on Linux CI and on Windows and the pytest process's own priority never changes; (b) one subprocess test runs the real function twice in a child interpreter (sys.executable, PYTHONPATH at src, timeout 60 s) that prints its own priority after each call: the two readings are equal and are niceness >= 10 on POSIX or class 0x4000 on Windows. Fails on master (no module); mutation-proven guard: removing the at-or-below check fails the twice tests, removing the exception guard fails the refusal tests."
  - "P3 (the hard-coded six goes). Property: `warm_then_fan_out` (src/spec_agents/caching.py:74) and `map_agent` (src/spec_agents/agents/parallel.py:76) default `max_workers` to None and size the pool from `budget.workers()` at call time; a caller that passes `max_workers` gets exactly today's pool, `max(1, min(max_workers, pending))`. Test: tests/test_budget.py records the `max_workers` that `ThreadPoolExecutor` receives (monkeypatched in `spec_agents.caching`, no timing): with `SPEC_AGENTS_WORKERS=2` set after import, five tasks with warm=False get a pool of 2 through each function, and an explicit `max_workers=4` still gets 4. Fails on master (the default is 6, so the pool is 5). tests/test_caching.py and tests/test_parallel.py pass unedited."
files:
  touched:
    - src/spec_agents/budget.py               # NEW: workers(), below_normal()
    - src/spec_agents/caching.py              # warm_then_fan_out's max_workers default and its docstring line only
    - src/spec_agents/agents/parallel.py      # map_agent's max_workers default and its docstring line only
    - src/spec_agents/__init__.py             # one `budget` line in the Submodules docstring only
    - AGENTS.md                               # the public-surface list (:86) names spec_agents.budget; nothing else
    - tests/test_budget.py                    # NEW: P1, P2, P3 tests
    - docs/CURRENT_STATE.md                   # a new `## As of` section only, if the drift-audit hook refuses a commit
    - .agent/tasks/spec-agents-budget-1.md
    - .agent/verifications/spec-agents-budget-1.md
  must-not-touch:
    - pyproject.toml                          # no version bump, no psutil dependency or extra (operator cut)
    - .github/workflows/ci.yml                # psutil resolves through pyright's bundled stubs (measured): no CI change
    - tests/test_caching.py                   # passes unedited (no test pins six: measured)
    - tests/test_parallel.py                  # passes unedited
    - scripts/bump_consumers.py               # no consumer bump
    - "The `__version__` line of src/spec_agents/__init__.py: it stays 0.12.0"
    - "The generated:repo-facts block of docs/CURRENT_STATE.md: it is machine-written"
---
# spec-agents-budget-1: pools that fit the machine, and a way to step aside

## Why
Outcome: spec_agents' fan-out pools fit the box they run on, and a long batch can lower its own priority.
Today both pools default to a hard-coded six whatever the machine. Source: planning `agent-task/queue.toml`
`spec-agents-budget-1` (operator-approved 2026-10-02, item E2).

## Measured (origin/master ed24ae9; Windows 10, Python 3.12, os.cpu_count() = 12, so workers() = 8 here)
- The only worker counts in src/ are `max_workers: int = 6` at caching.py:74 and parallel.py:76; map_agent passes
  it through (parallel.py:167) and the pool is built at caching.py:117-118. Nothing in src/ uses ProcessPoolExecutor,
  os.cpu_count or a priority call. No test pins six: test_caching.py:51,87 and test_parallel.py:62,280 pass 4 or 5.
- No runtime environment variable is read in src/ outside secrets.get_secret; the one `SPEC_AGENTS_` name in the
  repo is `SPEC_AGENTS_TOKEN` (docs/CURRENT_STATE.md), hence `SPEC_AGENTS_WORKERS`.
- psutil is not a dependency (pyproject.toml) and CI does not install it (ci.yml: `.[dev,textual]` + keyring). This
  box's Python312 has psutil 7.1.3; planning's .venv has none. pyright 1.1.411 on a lazy `import psutil` with psutil
  absent: 0 errors, 1 warning (reportMissingModuleSource; bundled typeshed stubs), exit 0.
- No `changes/` directory or CHANGELOG in this repo. The drift-audit pre-commit hook refuses a commit once the
  newest `## As of` in docs/CURRENT_STATE.md is over 3 days old; the spec commit added one dated 2026-10-02.

## Out of scope
- No SQLite queue, no GPU semaphore, no ONNX (operator cut).
- No version bump and no consumer bump: the three consumers stay on v0.12.0.

## Notes
- The driver is orchestrator [07dbfb]. Report by commit + `sprint_heartbeat.py --state completed|failed|input-required`
  (planning/scripts); SendMessage orchestrator [07dbfb] is the fast path for a question. Stop at ready-to-merge: the
  driver reviews and merges. `git push` is the driver's job.
- Interpreter: C:/Users/ghendrick/AppData/Local/Programs/Python/Python312/python.exe with PYTHONPATH=src; never
  `pip install -e` (a shared editable install races worktrees). One pytest at a time; record the baseline count first.
- Gates: ruff 0.16.6 (`check` and `format --check`), pyright 1.1.411 with `--pythonpath <interpreter>`, pytest -q.
- Branch on `sys.platform == "win32"`, not os.name: typeshed declares `os.nice` POSIX-only and `ctypes.windll`
  Windows-only, and only a sys.platform check lets pyright narrow on both OSes.
- Bound every reproduction (the subprocess test's timeout included); never lower the pytest process's own priority;
  stop only PIDs you started; leave no probe file.
- Before ready-to-merge, run /code-review on a detached copy of the branch and list what was fixed or left in the
  verification doc's `## Self-review`.
- QUESTION (P1's default applies unless the driver answers otherwise): a bad explicit value (`SPEC_AGENTS_WORKERS=abc`,
  `0`, or `workers(0)`) raises ValueError naming its source, or falls back to the machine default? Recommended: raise,
  as v0.11.1's fail_severity guard does, so a typo never passes silently.
