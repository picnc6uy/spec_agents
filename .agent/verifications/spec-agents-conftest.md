---
task-id: spec-agents-conftest
verified: 2026-05-28
status: ready-to-merge
agent: claude-code
---

# Verification for spec-agents-conftest

## Automated checks

- [x] `pytest -q` — **67 passed in 1.43s** with NO `PYTHONPATH` env
  override. Command: `python -m pytest -q`. This is the whole point
  of the change: worktree tests now resolve `spec_agents` to
  `worktree/src/` automatically.
- [x] `ruff check tests/conftest.py` — **"All checks passed!"**.
- [x] `ruff format --check tests/conftest.py` — **"1 file already formatted"**.
- [x] `pyright .` — n/a for `tests/conftest.py` (not in `pyproject.toml`
  `include` list; pyright runs on `src/` only per project convention).
- [x] `git diff --name-only HEAD` matches `files.touched`:
  ```
  tests/conftest.py    (new file)
  ```
  Plus `.agent/tasks/spec-agents-conftest.md` (scaffold from
  `agent-task new`; expected — not in must-not-touch).

## Acceptance criteria

- [x] **`tests/conftest.py` exists with a `sys.path` insert pointing at `../src`.**
  Evidence: `tests/conftest.py:18-21`. Pattern mirrors
  `spectacular/tests/conftest.py:14-16` and
  `personal_os/tests/conftest.py:12-14` verbatim. Idempotent guard
  (`if str(_SRC) not in sys.path`) prevents double-insert.

- [x] **`pytest -q` passes 67 tests with NO `PYTHONPATH` override.**
  Evidence: see Automated checks. Pre-conftest sanity reference: in
  the prior `spec-agents-lens-validator` worktree (commit
  `2363ef4`), `pytest -q` without `PYTHONPATH` failed at collection
  with `ImportError: cannot import name 'ValidationIssue' from
  'spec_agents.knowledge.lenses'` (resolving to site-packages). The
  workaround was `PYTHONPATH=src pytest`. This PR makes that
  workaround unnecessary.

- [x] **`ruff check + ruff format check` clean on the new file.**
  Evidence: see Automated checks.

- [x] **No changes to `src/` or any existing `tests/test_*.py` file.**
  Evidence: `git diff --name-only HEAD` returns only
  `tests/conftest.py`. The 10 `tests/test_*.py` files in
  `must-not-touch` are all unmodified. `src/` tree untouched.

- [x] **No changes to `pyproject.toml`.**
  Evidence: same `git diff`. The alternative
  `[tool.pytest.ini_options] pythonpath = ["src"]` was considered
  but rejected in scope to keep the change a strict mirror of
  sibling repos.

## Out-of-scope confirmation

- [x] **No files in `files.must-not-touch` were modified.**
  Evidence: `git diff --name-only HEAD` returns one file
  (`tests/conftest.py`, which IS in `files.touched`). The
  must-not-touch list (`src/`, all `tests/test_*.py`, `pyproject.toml`,
  `docs/`, `.agent/lenses/`, `.agent/README.md`,
  `.agent/{task,verification}-template.md`, other repos) is entirely
  untouched.

## Things I deliberately did not do

- **Touched `docs/CURRENT_STATE.md`.** The prior sprint already bumped
  it to reflect the post-validator state (test count 67, master commit
  `792f116`, public-surface entry for `ValidationIssue`). This PR adds
  no public-surface symbol and doesn't move the test count; no doc
  refresh needed. The master-commit line will be slightly stale after
  this PR ff-merges (pointing at `792f116` rather than the new merge
  SHA), but the drift-audit hook permits ≤3 days of staleness and this
  is the same day. The next drift refresh will pick up both this PR
  and the validator PR together.
- **Bumped `pyproject.toml` version.** Pre-existing drift (declares
  `0.4.0`; tags + CURRENT_STATE claim `v0.6.0`) — flagged in the
  prior verification doc, still not in scope.
- **Fixed the pyright `Config "strict" entry must contain an array`**
  config warning. Same story — pre-existing, separate task.
- **Added shared pytest fixtures.** spectacular and personal_os
  conftests include domain fixtures (`in_memory_db`, etc.); spec_agents
  kernel intentionally does not — fixtures belong to consumers, the
  kernel exposes `spec_agents.testing.db` as a primitive.

## Risks for human reviewer

1. **Editable-install interaction.** If the operator later runs
   `pip install -e .` in spec_agents, that creates a site-packages
   entry that ALSO resolves `spec_agents` (via the egg-link or
   `.pth` file). My `sys.path.insert(0, ...)` ensures the worktree
   `src/` comes FIRST, so it wins. But if the editable install ever
   gets a different layout (e.g., `src-layout` switched to flat
   layout), the path math (`parents[1] / "src"`) breaks. Low risk
   today; flag for the inevitable layout refactor.

2. **No pyright check on `tests/`.** The conftest itself is
   trivial enough that this doesn't matter, but if future test
   bootstrapping grows complex, consider adding `tests/` to the
   pyright `include` list. Out of scope here.

3. **One-shot fix; no regression test.** There's no test that
   *checks* that `pytest` works without `PYTHONPATH`. The proof is
   running pytest itself — which we do in CI. If the conftest
   regresses (e.g., import removed, path math wrong), CI breaks at
   collection. Acceptable: the failure mode is loud and immediate.

## Documentation drift (per the drift-audit lens)

- [x] **`docs/CURRENT_STATE.md` in this repo still matches reality.**
  Test count 67 unchanged; public-surface unchanged; only the master
  commit line will be one PR behind after merge (same-day; the
  drift-audit hook permits this).
- [x] **Cross-repo claims this change affects.** Verification doc of
  the prior sprint at
  `spec_agents/.agent/verifications/spec-agents-lens-validator.md`
  recommended this exact follow-up. Now closed.
- [x] **Memory entries.** None reference `tests/conftest.py`.
- [x] **All path references resolve.**

## Diff summary

- 1 file changed (new), +24 lines, −0 lines:
  - `tests/conftest.py` — sys.path insert with idempotent guard,
    mirrors sibling repos' pattern. No fixtures (kernel-freeze).

Plus 1 new file: `.agent/tasks/spec-agents-conftest.md` (scaffold
from `agent-task new`, filled in by this agent).

## Verdict

**Ready to merge.** Pure-refactor scope: no behavior change in `src/`,
no test changes, no public-surface delta. Test discovery now matches
sibling repos. The `PYTHONPATH=src` workaround documented in the
prior sprint's verification doc is no longer needed.
