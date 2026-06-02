---
id: verify-fail-severity-guard
title: verify() silently passes on a typo'd fail_severity — validate the threshold
type: bug-fix
lens: bug-fix
created: 2026-06-01
status: drafted
budget:
  max_iterations: 20
  max_cost_usd: 2   # stub-only unit test; no API
  on_breach: abort-to-needs-rework
acceptance:
  - "Reproduction test (fails on current code): verify(rules=[<rule returning an 'error' issue>], fail_severity='errrn') currently returns passed=True — a verification that cannot fail. Test asserts the fixed behavior: a ValueError is raised."
  - "verify() validates fail_severity at entry: raises ValueError naming the bad value + the valid set when fail_severity not in _SEVERITY_RANK. Signature unchanged."
  - "Known thresholds still behave: fail_severity='error' (default) and 'warning' (strict) produce the same passed results as before."
  - "Issue severities keep the SAFE asymmetry: an unknown ISSUE severity still ranks high and fails (a typo'd issue can't hide); only the THRESHOLD is validated."
  - "verify_schema / verify_evidence (which forward fail_severity to verify) inherit the guard — a typo'd threshold raises there too."
  - "All existing tests pass; ruff + pyright (pinned, strict) clean; collected-test count strictly increases. Patch version bump 0.11.0 -> 0.11.1 + CURRENT_STATE note."
files:
  touched:
    - src/spec_agents/agents/verifiers.py
    - tests/test_verifiers.py
    - docs/CURRENT_STATE.md
    - pyproject.toml
    - .agent/tasks/verify-fail-severity-guard.md
    - .agent/verifications/verify-fail-severity-guard.md
  must-not-touch:
    - src/spec_agents/usage.py
    - src/spec_agents/agents/parallel.py
    - src/spec_agents/agents/critic.py
---

# verify-fail-severity-guard: validate verify()'s fail_severity threshold

## Why
The code_review_swarm dogfood review of spec_agents found a real **[medium]** bug: `_at_or_above`
(verifiers.py:109) ranks an unknown severity at 99. That's the SAFE direction for an *issue* severity
(a typo'd issue ranks high → fails). But it's applied to the **threshold** too:
`_SEVERITY_RANK.get(fail_severity, 99)`. So a **typo'd `fail_severity` ranks 99**, no real issue (rank
≤3) meets it, and `verify()` returns `passed=True` **even with real errors present** — a verification
that silently cannot fail. This is a textbook "trusted-signal-isn't-real" footgun.

## What
Smallest fix: validate the threshold at `verify()` entry.
```python
def verify(*, rules, fail_severity="error"):
    if fail_severity not in _SEVERITY_RANK:
        raise ValueError(
            f"unknown fail_severity {fail_severity!r}; expected one of {sorted(_SEVERITY_RANK)}"
        )
    ...
```
- Signature unchanged (still keyword-only `rules`, `fail_severity`).
- `_at_or_above`'s `get(severity, 99)` for the ISSUE arg stays — that asymmetry is the intended safe
  behavior (unknown issue severity → fails). Only the threshold is now guaranteed-known.
- `verify_schema`/`verify_evidence` forward `fail_severity` to `verify()`, so they inherit the guard
  without their own change. Tighten the `_at_or_above` docstring to note the threshold is validated upstream.

## Out of scope
- Validating issue severities (the unknown-ranks-high default is deliberately safe there).
- Changing `verify()`'s signature, the `_SEVERITY_RANK` scale, or the wrappers' signatures.
- The code_review_swarm tool itself (separate repo / sprints).

## Notes
- Bug-fix lens: failing test first (typo'd threshold currently passes-with-errors → after fix raises).
- Longstanding issue (not a regression) — present since SA-003 shipped; exposed by the swarm review.
- Preventative rec (backlog, not this task): a coverage rule asserting every public threshold/enum arg
  is validated, or make `fail_severity` a Literal/enum so a typo is a type error.

## References
- Found by: `planning/scripts/code_review_swarm.py` spec_agents run (`reviews/spec_agents-2026-06-01/`).
- Bug site: `src/spec_agents/agents/verifiers.py:105-151`.
