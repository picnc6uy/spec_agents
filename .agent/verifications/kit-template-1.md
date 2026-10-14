---
task-id: kit-template-1
verified: 2026-10-14
status: ready-to-merge
agent: claude-code
---

# Verification for kit-template-1

Interpreter: `C:\Users\ghendrick\AppData\Local\Programs\Python\Python312\python.exe` (3.12), Python312 and Scripts first on PATH. No SKIP=.

## Automated checks
- [x] `pytest -q` -- 194 passed.
- [x] `ruff check .` and `ruff format --check .` -- clean.
- [x] `pyright` -- 0 errors, 0 warnings.
- [x] `pre-commit run --all-files` in this repo -- passes.

## Acceptance criteria
- [x] P1 -- `tests/test_new_repo.py::test_generated_repo_passes_its_own_gates_on_first_commit` generates into tmp_path, then runs the new repo's `pre-commit run --all-files` (all 12 hooks pass) and `python -m pytest -q` (1 passed). Same by hand into the scratchpad `tmpl-check/tmpl-demo`.
- [x] P2 -- the same test compares the three scripts to `planning/agent-task/scripts` (CRLF folded to LF, as planning's conformance check compares them).
- [x] P3 -- generator imports stdlib only; it runs `git init/add/commit` and the Forge installer; no remote, no network.

## Conformance check on the generated repo
Every column in planning `check_stack_conformance.CHECKS` passes except `repo-facts=fresh` (the daily 07:00 job writes the block) and `backed up` (no remote by design). The repo is not in `CANONICAL_REPOS`; adding it is an operator edit in planning.

## Things I deliberately did not do
Step 1 of the extraction plan (drift checks as kit hooks) was dropped by the operator; the drift scripts are copied, not referenced. No pyright pre-push hook in the template (spec_agents has none).
