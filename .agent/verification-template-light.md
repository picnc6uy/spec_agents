---
task-id: T-XXX
verified: YYYY-MM-DD
status: draft
agent: claude-code
tier: light
---

# Verification for T-XXX (light tier)

Light tier = low blast radius (see agent-task/README.md "Verification
tiers"). State why this qualifies in one line; if you can't, use the full
template instead.

**Tier justification:** <one line: who breaks if this is wrong, and when
do they find out?>

## Gates (paste real output, not summaries)
- [ ] `pytest -q` — <count> (was <count> before; new tests: <n>)
- [ ] `ruff check` / `pyright` — <pass/fail>
- [ ] `git diff --name-only main..HEAD` ⊆ `files.touched`; nothing in must-not-touch

## Acceptance — one line each
<criterion> → <met/not met + the single most convincing fact>

## Honesty list
<Anything skipped, deferred, or known-weak. "Nothing" is fine if true.>

## Spec interpretation notes
<Any reasonable divergence from the spec's literal wording, and why. "None" if exact.>

## Verdict
<"Ready to merge" or "Needs rework: <reason>".>
