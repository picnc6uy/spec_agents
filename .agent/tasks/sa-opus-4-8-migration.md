---
id: sa-opus-4-8-migration
title: Migrate plan_then_act docstring example from claude-opus-4-7 to claude-opus-4-8
type: refactor
lens: refactor
created: 2026-05-28
status: drafted
acceptance:
  - "`plan_then_act.py` docstring example uses `claude-opus-4-8` (was: `claude-opus-4-7`)"
  - "67 tests pass identically"
  - "ruff check + ruff format --check clean"
  - "no behavior change (the change is in a docstring example, not in function defaults)"
files:
  touched:
    - src/spec_agents/agents/plan_then_act.py
  must-not-touch:
    - src/spec_agents/ (except agents/plan_then_act.py)
    - tests/
    - docs/
    - pyproject.toml
    - .agent/
    - .secrets.baseline
    - any other repo
---

# sa-opus-4-8-migration: bump docstring example to claude-opus-4-8

## Why

Anthropic shipped **Opus 4.8** today (2026-05-28) at $5/$25 per MTok,
**3x cheaper** than Opus 4.7. Cross-stack migration `claude-opus-4-7` →
`claude-opus-4-8` is in flight; spec_agents' lone reference is the
docstring example in `plan_then_act.py` showing how callers invoke
the primitive.

The example shows `model="claude-opus-4-7"` — operators copy-pasting
the docstring would get the older model. Bump to current.

`plan_then_act` itself takes `model` as a required kwarg with no
default, so this change has zero behavior impact on the kernel — it's
purely a docs-quality bump.

## What

`src/spec_agents/agents/plan_then_act.py:34`:

```python
# Before
result = plan_then_act(
    client=client,
    model="claude-opus-4-7",
    ...
)

# After
result = plan_then_act(
    client=client,
    model="claude-opus-4-8",
    ...
)
```

That's it. Docstring example bump.

## Out of scope

- **Function default model.** The function signature has no default
  `model` — caller-supplied. Nothing to bump in the signature.
- **Other repos.** Spectacular has 5 source files + a constant in
  `audit_dag_ab.py` that need bumping. That's a separate sprint
  running immediately after this one.
- **CURRENT_STATE.md refresh.** Master commit already at `1e69636`
  (today's pyright config fix); same-day commits accepted by drift hook.
- **Version bump.** Docstring-example change is non-breaking.

## Notes

- Refactor-lens invariant: 67 tests pass before and after.
- Behavior identical: docstring example only; no function-body change.

## References

- `planning/architecture-reviews/2026-05-28-sonnet-audit.md` (with correction note appended)
- Memory entry `reference-model-tiers` — canonical pricing source
- Sibling sprint: spectacular cross-stack Opus migration (5 files + tracker)
