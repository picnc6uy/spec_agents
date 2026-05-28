---
id: spec-agents-version-bump
title: Sync pyproject.toml + __init__.py version to v0.6.0
type: refactor
lens: refactor
created: 2026-05-28
status: drafted
acceptance:
  - pyproject.toml version field reads "0.6.0"
  - src/spec_agents/__init__.py __version__ reads "0.6.0"
  - All existing tests pass with unchanged count
  - No other files changed
files:
  touched:
    - pyproject.toml
    - src/spec_agents/__init__.py
  must-not-touch:
    - docs/
    - .agent/
    - src/spec_agents/ (except __init__.py)
    - tests/
---

# spec-agents-version-bump: Sync pyproject.toml + __init__.py version to v0.6.0

## Why

`pyproject.toml` and `src/spec_agents/__init__.py` both read `"0.4.0"` while
the repo has been tagged through `v0.6.0`. Consumers that pin
`spec-agents @ git+https://...@v0.6.0` get the correct code, but the package
metadata reports the wrong version — which confuses `pip show`, `importlib.metadata`,
and any tooling that reads `__version__`. This task closes the drift with a
two-line change.

## What

Change exactly two strings:

1. `pyproject.toml` line 7: `version = "0.4.0"` → `version = "0.6.0"`
2. `src/spec_agents/__init__.py` line 19: `__version__ = "0.4.0"` → `__version__ = "0.6.0"`

No logic changes, no dependency changes, no new exports. A single commit on
`agent/spec-agents-version-bump` is sufficient — there are only two lines.

## Out of scope

- Bumping to v0.7.0 or tagging a new release (separate task when new features land)
- Updating consumer pins in personal_os, photo_archive, spectacular
- Touching `docs/CURRENT_STATE.md` — the "0.4.0" mention there is accurate historical
  narrative describing what shipped in SA-003, not a live version reference
- Any changes inside `tests/`, `.agent/verifications/`, or `.agent/tasks/`

## Notes

`docs/CURRENT_STATE.md:97` references `v0.4.0` in the sentence "SA-003 (verifiers,
v0.4.0)" — this is correct history and must not change.

The refactor lens sanity check (`git stash && pytest -q && git stash pop; pytest -q`)
is overkill for a two-line string change but run it anyway to satisfy the lens
contract — expect identical test counts before and after.

## References
- HANDOVER.md "What's already done" — SA-003 shipped at v0.4.0 tag; v0.5.0 + v0.6.0
  tagged subsequently without a pyproject.toml bump
