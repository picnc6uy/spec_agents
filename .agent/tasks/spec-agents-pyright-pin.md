---
id: spec-agents-pyright-pin
title: Add pyright==1.1.360 to dev extras to match CI (stack-wide pin)
type: refactor
lens: refactor
created: 2026-05-28
status: drafted
acceptance:
  - "dev extra adds pyright==1.1.360 (matches CI pin)"
  - "pytest -q unchanged + green; pyright 0 errors at 1.1.360"
files:
  touched:
    - pyproject.toml
    - docs/CURRENT_STATE.md
    - .agent/tasks/spec-agents-pyright-pin.md
    - .agent/verifications/spec-agents-pyright-pin.md
  must-not-touch:
    - src/
    - tests/
    - .github/workflows/ci.yml
---

# spec-agents-pyright-pin: pin pyright in dev extras

## Why
Stack-wide pin (review Open Q5, operator chose pin-exact). CI already installs
`pyright==1.1.360`, but the dev extra didn't declare pyright at all, so `pip install .[dev]`
gave no pyright (manual install → drift risk). Adding the pinned dep makes a local `.[dev]`
reproduce CI's type-check exactly.

## What
Add `pyright==1.1.360` to the `dev` optional-dependencies. Config-only; no behavior change.

## Out of scope
- CI workflow (already pins 1.1.360). src/ and tests/.

## References
- planning/architecture-reviews/2026-05-28-comprehensive-review-synthesis.md (Open Q5)
