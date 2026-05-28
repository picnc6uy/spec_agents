---
id: spec-agents-pyright-config-fix
title: Fix malformed pyright `strict = true` config (should be empty array) — sibling of spectacular fix
type: refactor
lens: refactor
created: 2026-05-28
status: drafted
acceptance:
  - "pyproject.toml `[tool.pyright]` has `strict = []` (valid empty array)"
  - "pyright runs without the 'Config strict entry must contain an array' warning"
  - "pyright error count unchanged: 0 → 0 (same default-mode behavior)"
  - "67 tests pass identically"
  - "no `src/`, `tests/`, or `docs/` changes"
files:
  touched:
    - pyproject.toml
  must-not-touch:
    - src/
    - tests/
    - docs/
    - .agent/
    - .secrets.baseline
    - any other repo
---

# spec-agents-pyright-config-fix: replace `strict = true` with `strict = []`

## Why

Sibling to spectacular's `spec-pyright-config-fix` (shipped today
`183218a` → fast-forward-merged into spectacular/master). spec_agents'
`[tool.pyright]` block has the same malformed `strict = true` — discovered
during today's cross-stack scan in `planning/architecture-reviews/2026-05-28-autonomous-run-findings.md` §1.

The bug: pyright wants an array of paths, not a boolean. It emits "Config
'strict' entry must contain an array." and silently ignores the
directive — running default-mode on `include` instead. Less visible
in spec_agents than in spectacular because spec_agents pyright reports
0 errors either way (small surface, well-typed code), but the config
is still wrong.

Same fix pattern: `strict = []` — valid empty array, preserves current
default-mode behavior.

## What

One file, one string change:

`pyproject.toml` `[tool.pyright]` block:

```toml
# Before
strict = true

# After
strict = []
```

That's it. No other config changes. No file graduations.

After this PR:
- `pyright` emits no config warning.
- 0 pyright errors remain.
- CI behavior unchanged.

## Out of scope

- **Adding paths to `strict = []`** to actually graduate modules.
  spec_agents has the full `src/` already in `include`; populating
  `strict = ["src"]` (or similar) would put the kernel's full public
  surface into strict mode and may surface new errors. Operator-
  decision; not this PR.
- **Any `src/` or `tests/` changes.**
- **CURRENT_STATE.md refresh** — master commit already at `a92080d`
  (today's v0.7.0 bump), date 2026-05-28. Same-day commits pass the
  drift-audit hook without re-bumping.

## Notes

- Refactor-lens invariant: 67 tests pass before and after.
- pyright error count: 0 → 0.
- The sibling spectacular fix shipped today `183218a` is the model;
  this PR is the same shape on a different repo.

## References

- `planning/architecture-reviews/2026-05-28-autonomous-run-findings.md` §1
- Sibling fix: `spectacular/agent/spec-pyright-config-fix` (closed `183218a`)
- pyright config docs: https://microsoft.github.io/pyright/#/configuration
