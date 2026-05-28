---
id: spec-agents-version-bump
title: Bump version to v0.7.0 (LensLoader.validate + ValidationIssue public surface)
type: refactor
lens: refactor
created: 2026-05-28
status: drafted
acceptance:
  - pyproject.toml version field reads "0.7.0"
  - src/spec_agents/__init__.py __version__ reads "0.7.0"
  - CURRENT_STATE.md Tag line names v0.7.0, dated 2026-05-28, notes "adds LensLoader.validate() + ValidationIssue dataclass"
  - CURRENT_STATE.md consumer-pin URL updated to @v0.7.0
  - pytest -q clean (67 passing; behavior unchanged)
  - ruff + ruff-format clean
files:
  touched:
    - pyproject.toml
    - src/spec_agents/__init__.py
    - docs/CURRENT_STATE.md
  must-not-touch:
    - .agent/
    - src/spec_agents/ (except __init__.py)
    - tests/
---

# spec-agents-version-bump: Bump version to v0.7.0

## Why

`pyproject.toml` and `__init__.__version__` are stuck at `"0.4.0"` while the
repo is tagged through `v0.6.0`, and `spec-agents-lens-validator` added
`LensLoader.validate()` + `ValidationIssue` to the public surface on 2026-05-28
(post-v0.6.0). Per SemVer MINOR rules and CURRENT_STATE.md's own "Bump version
on any further public-surface change" rule, the correct target is `v0.7.0` — not
v0.6.0 (which would close the metadata drift but immediately reopen it).
`docs/CURRENT_STATE.md` also needs its Tag line and consumer-pin URL updated
to match.

## What

Three files, five string changes:

1. `pyproject.toml:7`: `version = "0.4.0"` → `version = "0.7.0"`
2. `src/spec_agents/__init__.py:19`: `__version__ = "0.4.0"` → `__version__ = "0.7.0"`
3. `docs/CURRENT_STATE.md` Tag block: replace the v0.6.0 tag line with a v0.7.0
   line dated 2026-05-28 noting "adds `LensLoader.validate()` + `ValidationIssue`
   dataclass". Consumer-pin URL changes from `@v0.6.0` → `@v0.7.0`.

No logic changes, no dependency changes, no test changes.

Operator post-merge action (NOT part of this PR): `git tag v0.7.0 && git push origin v0.7.0`.
The tag is what unblocks consumers to bump their pins; the PR only changes the strings.

## Out of scope

- Updating consumer pins in personal_os, photo_archive, spectacular (separate task)
- Adding `spec-agents-lens-validator` to the Active Sprint history list in
  CURRENT_STATE.md (already documented in the Public Surface section)
- Any changes inside `tests/`, `.agent/`

## Notes

`docs/CURRENT_STATE.md:97` references `v0.4.0` in "SA-003 (verifiers, v0.4.0)"
— that's accurate historical narrative; do not touch it.

The Active Sprint section's "SA-004 (plan-then-act, v0.6.0)" is also history;
leave it.

## References
- Operator redirect 2026-05-28: v0.7.0 not v0.6.0 — LensLoader.validate +
  ValidationIssue added post-v0.6.0; SemVer MINOR bump required
- CURRENT_STATE.md "Bump version on any further public-surface change" rule
