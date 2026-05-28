---
task-id: spec-agents-version-bump
verified: 2026-05-28
status: ready-to-merge
agent: claude-code
---

# Verification for spec-agents-version-bump

## Automated checks
- [x] `py -3.12 -m pytest -q` — **67 passed** (behavior unchanged)
- [x] `py -3.12 -m pyright src` — 18 errors, 0 warnings. Pre-existing (environment missing sqlalchemy/anthropic for pyright; same count before this branch). No new errors introduced.
- [x] `py -3.12 -m ruff check .` — All checks passed
- [x] `py -3.12 -m ruff format --check .` — 33 files already formatted
- [x] `git diff --name-only HEAD~2..HEAD` matches `files.touched`

## Acceptance criteria

- [x] `pyproject.toml` version field reads "0.7.0"
  Evidence: `pyproject.toml:7` — `version = "0.7.0"`

- [x] `src/spec_agents/__init__.py` `__version__` reads "0.7.0"
  Evidence: `src/spec_agents/__init__.py:19` — `__version__ = "0.7.0"`

- [x] CURRENT_STATE.md Tag line names v0.7.0, dated 2026-05-28, notes "adds LensLoader.validate() + ValidationIssue dataclass"
  Evidence: `docs/CURRENT_STATE.md:13-17` — Tag block replaced; reads:
  "`v0.7.0` (2026-05-28, adds `LensLoader.validate()` + `ValidationIssue` dataclass — spec-agents-lens-validator, closes Move 1 of D-citations-files-pdf DECLINE)"

- [x] CURRENT_STATE.md consumer-pin URL updated to @v0.7.0
  Evidence: `docs/CURRENT_STATE.md:16` — `@v0.7.0`

- [x] pytest -q clean (67 passing; behavior unchanged)
  Evidence: see Automated checks above

- [x] ruff + ruff-format clean
  Evidence: see Automated checks above

## Out-of-scope confirmation
- [x] No files in `files.must-not-touch` were modified
  Evidence: only `pyproject.toml`, `src/spec_agents/__init__.py`, `docs/CURRENT_STATE.md` changed.
  `docs/CURRENT_STATE.md:97` "SA-003 (verifiers, v0.4.0)" — accurate history, not changed.
  Active Sprint "SA-004 (plan-then-act, v0.6.0)" — accurate history, not changed.
  `tests/` unchanged. `.agent/` unchanged (task spec + verification are tracked separately).

## Things I deliberately did not do
- Did not update consumer pins in personal_os / photo_archive / spectacular (separate task)
- Did not add a v0.7.0 git tag — that is an operator post-merge action per repo convention
- Did not fix the pre-existing 18 pyright import errors (environment issue, different scope)

## Risks for human reviewer
- The operator must run `git tag v0.7.0 && git push origin v0.7.0` after merge — the PR only changes version strings; consumer pin bumps are blocked on the tag existing.
- Pyright 18 errors are pre-existing environment noise (missing sqlalchemy/anthropic in pyright's Python env). Confirm with `git stash && py -3.12 -m pyright src` if needed.

## Documentation drift (per the drift-audit lens)
- [x] `docs/CURRENT_STATE.md` updated in this task — Tag line and consumer pin now reflect v0.7.0.
- [x] `planning/HANDOVER.md` — no update needed; HANDOVER names v0.6.0 as the current tag (accurate until the operator runs `git tag v0.7.0`; HANDOVER update is post-merge/post-tag, not in this PR).
- [x] All path references resolve.

## Diff summary
- 3 files changed, ~7 / ~5 lines
- `pyproject.toml:7`: `"0.4.0"` → `"0.7.0"`
- `src/spec_agents/__init__.py:19`: `"0.4.0"` → `"0.7.0"`
- `docs/CURRENT_STATE.md:13-17`: Tag block — v0.6.0 / SA-004 description → v0.7.0 / LensLoader.validate() note; consumer pin @v0.6.0 → @v0.7.0

## Verdict
Ready to merge.
