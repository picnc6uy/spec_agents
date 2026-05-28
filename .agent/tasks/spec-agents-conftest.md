---
id: spec-agents-conftest
title: Add tests/conftest.py to make pytest find worktree src/ without PYTHONPATH
type: refactor
lens: refactor
created: 2026-05-28
status: drafted
acceptance:
  - "tests/conftest.py exists with a sys.path insert pointing at ../src"
  - "pytest -q passes 67 tests with NO PYTHONPATH override (the change is self-sufficient)"
  - "ruff check + ruff format check clean on the new file"
  - "no changes to src/ or any existing tests/test_*.py file"
  - "no changes to pyproject.toml (kernel-freeze; no test-config knob bumped)"
files:
  touched:
    - tests/conftest.py
  must-not-touch:
    - src/
    - tests/test_adapter.py
    - tests/test_batch.py
    - tests/test_critic.py
    - tests/test_eval.py
    - tests/test_imports.py
    - tests/test_lenses.py
    - tests/test_messages.py
    - tests/test_plan_then_act.py
    - tests/test_testing_db.py
    - tests/test_verifiers.py
    - pyproject.toml
    - docs/
    - .agent/lenses/
    - .agent/README.md
    - .agent/task-template.md
    - .agent/verification-template.md
    - any other repo
---

# spec-agents-conftest: Add tests/conftest.py for worktree-src imports

## Why

Follow-up flagged in `spec-agents-lens-validator` verification doc
(2026-05-28). spec_agents has no `tests/conftest.py`; pytest therefore
imports `spec_agents` from the pip-installed copy in
`site-packages/`, not from the worktree's `src/`. Effect: when an
agent-task worktree introduces new public-surface symbols (e.g.,
`ValidationIssue`), the tests fail to collect (`ImportError`) unless
the operator sets `PYTHONPATH=src` manually. CI may also stumble
depending on its install pattern.

The 2026-05-21 cycle retro added `tests/conftest.py` to spectacular,
personal_os, photo_archive, and one other — spec_agents was missed.
This closes that gap.

## What

Add a single file: `tests/conftest.py`. Five lines:

```python
"""Make spec_agents importable from src/ without an editable install.

Mirrors the pattern used by sibling repos so worktree-based
agent-task runs find the in-tree code, not the installed wheel.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

That's it. No `src/` changes, no test changes, no pyproject changes.
Pure test-discovery infrastructure.

After the change:
- `pytest -q` (no env var) → **67 passing**.
- `PYTHONPATH=src pytest -q` → still 67 passing (no-op override).
- `pip install -e .` workflow → still works (the inserted path comes
  first in sys.path; editable install resolves the same source).

## Out of scope

- **Behavior changes in `src/`.** This is a pure-refactor of test
  bootstrapping; no production code moves.
- **Pyproject `[tool.pytest.ini_options]` pythonpath setting.** That
  would achieve the same effect via a different mechanism. Sibling
  repos use the conftest.py pattern, so this one matches for
  consistency. Out of scope to change either way.
- **Fixing the pre-existing `pyproject.toml` version drift**
  (`0.4.0` declared vs `v0.6.0` tagged). Flagged in the prior
  verification; still not in scope here.
- **Fixing the pre-existing pyright config warning** ("Config
  'strict' entry must contain an array"). Same — flagged, not fixed.
- **`docs/CURRENT_STATE.md` refresh.** Test count stays at 67
  (unchanged from prior sprint); no public-surface change; no
  master-commit bump needed because the drift-audit hook compares
  doc-date vs commits-since (the doc-date will be refreshed by the
  drift hook only if MORE than 3 days have passed; today's commit is
  same-day as the prior refresh and master-commit will be
  bumped naturally at next drift refresh).

## Notes

- **Pattern fidelity.** Confirm the exact pattern in spectacular's or
  personal_os's `tests/conftest.py` before writing this one — sibling
  consistency matters. Likely identical to the snippet above; if
  there are extra imports (fixtures, structlog config), this conftest
  STAYS minimal — sibling repos add fixtures; spec_agents
  intentionally does not (per its kernel-freeze posture).
- **Sanity check per refactor lens.** Before and after test counts
  must match. Pre-conftest count is install-state-dependent:
  if `site-packages/spec_agents` is stale (missing
  `ValidationIssue`), pre-count is 0 (import error) — that's the
  *whole motivation* for this PR. Post-conftest count is
  deterministically 67. The verification doc cites both.
- **No public API surface affected.** `__all__` in
  `spec_agents.knowledge` and elsewhere is identical pre and post.

## References

- `planning/.agent/verifications/spec-agents-lens-validator.md`
  ("Things I deliberately did not do" → recommended this follow-up)
- Sibling pattern: `spectacular/tests/conftest.py`,
  `personal_os/tests/conftest.py`, `photo_archive/tests/conftest.py`
