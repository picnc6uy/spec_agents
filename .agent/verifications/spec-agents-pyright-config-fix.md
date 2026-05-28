---
task-id: spec-agents-pyright-config-fix
verified: 2026-05-28
status: ready-to-merge
agent: claude-code
---

# Verification for spec-agents-pyright-config-fix

## Automated checks

- [x] `pyright` — **0 errors, 0 warnings, 0 informations** post-fix.
  Baseline pre-fix: **0 errors + Config "strict" entry must contain an
  array warning**. Error count identical; the config warning is gone.
- [x] `pytest -q` — **67 passed in 1.23s** post-fix. Baseline pre-fix:
  **67 passed in 1.40s**. Identical count; refactor invariant held.
- [x] `git diff --name-only HEAD` matches `files.touched`:
  ```
  pyproject.toml
  ```

## Acceptance criteria

- [x] **pyproject.toml `[tool.pyright]` has `strict = []`.**
  Evidence: `pyproject.toml:29` — `strict = []  # pyright wants an
  array of paths here ...` with the same explanatory comment used in
  the spectacular sibling fix (`183218a`).

- [x] **pyright runs without the 'Config strict entry must contain an
  array' warning.**
  Evidence: post-fix output reads `0 errors, 0 warnings, 0 informations`
  — no config-warning line.

- [x] **pyright error count unchanged: 0 → 0.**
  Evidence: see Automated checks. No errors before or after; spec_agents'
  small surface is well-typed.

- [x] **67 tests pass identically.**
  Evidence: see Automated checks.

- [x] **No `src/`, `tests/`, or `docs/` changes.**
  Evidence: `git diff --name-only HEAD` returns only `pyproject.toml`.

## Out-of-scope confirmation

- [x] **No files in `files.must-not-touch` were modified.**
  Evidence: only `pyproject.toml` changed.

## Things I deliberately did not do

- **Did not populate `strict` with actual paths.** Putting `["src"]`
  in `strict` would put the kernel's entire public surface into strict
  mode and may surface errors I can't predict. Operator-decision
  territory; not this PR.

- **Did not touch `docs/CURRENT_STATE.md`.** Master commit already at
  `a92080d` (today's v0.7.0 bump). Same-day commits pass the drift-
  audit hook.

- **Did not bump `pyproject.toml` version.** No public-surface change.

## Risks for human reviewer

1. **Behavioral equivalence.** `strict = []` is equivalent to omitting
   the key. Pre-fix pyright was already silently default-mode (because
   `strict = true` was malformed); post-fix it's explicitly default
   mode. Same result.

2. **No CI impact.** CI runs pyright with whatever config pyproject
   specifies. Pre-fix CI ran default mode and saw 0 errors; post-fix
   it runs default mode and sees 0 errors.

3. **Future "graduate to actual strict" sprint** can populate
   `strict = [...]` when operator scopes it. Not this PR's problem.

## Documentation drift (per the drift-audit lens)

- [x] `docs/CURRENT_STATE.md` still matches reality.
- [x] Cross-repo claims: `planning/HANDOVER.md` doesn't claim anything
  specific about spec_agents' pyright config; no edit needed.
- [x] Memory entries: none reference spec_agents' pyright config.
- [x] All path references resolve.

## Diff summary

- 1 file changed, +3 / -1 lines:
  - `pyproject.toml:29`: `strict = true` → `strict = []` with a 2-line
    explanatory comment pointing at the findings memo.

Plus 2 new files from agent-task discipline.

## Verdict

**Ready to merge.** Same shape as the spectacular sibling fix
(`183218a`). Smallest correctness fix; same default-mode behavior;
config warning stopped. Closes Finding 1 / option 1 of the autonomous-
run findings memo for the spec_agents half.
