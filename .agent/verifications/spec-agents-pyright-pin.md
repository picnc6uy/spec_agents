---
task-id: spec-agents-pyright-pin
verified: 2026-05-28
status: ready-to-merge
agent: claude-code
---

# Verification for spec-agents-pyright-pin

## Automated checks
- [x] `pytest -q` — 73 passed in 1.64s (unchanged; config-only).
- [x] `pyright --pythonpath <Py312>` (1.1.360) — 0 errors, 0 warnings.
- [x] `ruff check .` — All checks passed.
- [x] diff matches files.touched (pyproject.toml, docs/CURRENT_STATE.md, .agent/).

## Acceptance criteria
- [x] dev extra adds `pyright==1.1.360`. Evidence: pyproject.toml dev list + comment.
- [x] pytest unchanged + green; pyright 0 errors at 1.1.360. Evidence above.

## Out-of-scope confirmation
- [x] No src/, tests/, or ci.yml change. Diff = pyproject + CURRENT_STATE + .agent/.

## Things I deliberately did not do
- Did not change CI (already pins 1.1.360).
- Opportunistic honesty fix (in the same CI line I was editing): corrected CURRENT_STATE
  "CI: pyright strict" → "pyright (default mode — strict = [])", which was the doc-honesty
  finding for this repo (the config is `strict = []`). Same-line, truthful, per the
  drift-audit "fix drift in the same commit" guidance. Flagging it explicitly here.

## Risks for human reviewer
- None material. Adds a pinned dev tool; no runtime or test impact.

## Documentation drift (per the drift-audit lens)
- [x] CURRENT_STATE CI line corrected (strict→default mode) + dev-pin noted. As-of date 2026-05-28 current.
- [~] master-commit line refresh deferred to the closing cross-repo drift pass.

## Diff summary
- 4 files: pyproject.toml (+pyright pin), CURRENT_STATE.md (CI line), task spec, verification.

## Verdict
Ready to merge. Config-only stack-wide pin + a same-line doc-honesty correction.
