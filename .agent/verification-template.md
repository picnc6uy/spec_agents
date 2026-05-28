---
task-id: T-XXX
verified: YYYY-MM-DD
status: draft
agent: claude-code
---

# Verification for T-XXX

## Automated checks
- [ ] `pytest -q` -- <pass/fail with count>
- [ ] `pyright .` (or `mypy .`) -- <pass/fail with count, or "n/a" if not configured>
- [ ] `ruff check .` -- <pass/fail>
- [ ] `git diff --name-only main..HEAD` matches `files.touched` in the task spec

## Acceptance criteria
<For each criterion listed in the task spec, restate it and provide evidence.>

- [ ] <criterion verbatim from task spec>
  Evidence: <command output, file paths, line numbers, or a one-line argument>

## Out-of-scope confirmation
- [ ] No files in `files.must-not-touch` were modified
  Evidence: `git diff --name-only main..HEAD` was cross-checked against the
  must-not-touch list.

## Things I deliberately did not do
<Anything that came up while doing the task but was outside scope. This is
the "while I was in here" honesty list. Saying "nothing" is fine if true.>

## Risks for human reviewer
<1-3 things the reviewer should think about. Concrete, not boilerplate.
"None identified" is a valid answer.>

## Documentation drift (per the drift-audit lens)
- [ ] `docs/CURRENT_STATE.md` in this repo still matches reality (master commit, test count, what's stubbed).
- [ ] Cross-repo claims this change affects (`planning/HANDOVER.md`, `planning/SYSTEM.md` status lines) are still accurate.
- [ ] Memory entries that reference state changed by this task have been updated, or a follow-up is noted below.
- [ ] All path references (charter, lenses, planning docs) still resolve.

If any box is unchecked: fix the drift in the same commit as the task
work, or in a preceding `docs:` commit on the same branch. Reference:
`planning/agent-task/agent-templates/lenses/drift-audit.md`.

## Diff summary
- N files changed, +M / -K lines
- <Highlights: what's new, what moved, what was renamed>

## Verdict
<One sentence: "Ready to merge" or "Needs rework: <reason>".>
