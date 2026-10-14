---
id: kit-template-1
title: Repo template + generator (kit extraction plan step 4)
type: new-feature
lens: new-feature
created: 2026-10-14
status: drafted
acceptance:
  - "P1. A repo made by scripts/new_repo.py passes its own `pre-commit run --all-files` and `py -3.12 -m pytest -q` on its first commit."
  - "P2. Its three agent-task script copies are byte-identical to planning/agent-task/scripts."
  - "P3. The generator is stdlib-only, makes no network call, adds no GitHub remote."
files:
  touched:
    - scripts/new_repo.py
    - templates/new_repo/**
    - tests/test_new_repo.py
    - pyproject.toml
    - docs/CURRENT_STATE.md
    - .agent/tasks/kit-template-1.md
    - .agent/verifications/kit-template-1.md
  must-not-touch:
    - src/spec_agents/**
    - the package version and release tags
    - the planning repo
---

Step 4 of "Kit extraction plan" in planning/reviews/2026-10-13-primitives-followup.md.
Step 1 (drift checks as kit hooks) was dropped: the drift scripts stay a byte-identical mirror.
