---
id: T-XXX
title: <short description>
type: <new-feature | refactor | bug-fix | security-review | architecture-review>
lens: <same as type, or a specific lens file name>
created: YYYY-MM-DD
status: drafted
acceptance:
  - <each acceptance criterion as a string>
files:
  touched:
    - <expected files/directories>
  must-not-touch:
    - <files/directories that must not change>
---

# T-XXX: <title>

## Why
<2-3 sentences. Why does this task exist? What's the user-visible outcome?
Link to design docs, prior PRs, or roadmap items if relevant.>

## What
<5-15 sentences. The actual change in concrete terms. Include API shapes,
function signatures, or schema diffs if the change is at that level.>

## Out of scope
<Explicit list. Things that LOOK related but aren't part of this task.
Be aggressive about scoping things out. "While I was in here" is the
enemy of a clean diff.>

## Notes
<Anything else: gotchas, prior art, decision rationale, constraints,
related-but-deferred work.>

## References
- <link to design doc, prior PR, issue, ADR, etc.>
