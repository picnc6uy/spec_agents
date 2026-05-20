# CLAUDE.md — spec_agents

> **Fresh session?** Start at [../planning/HANDOVER.md](../planning/HANDOVER.md) for the
> canonical session-start brief: project map, cross-repo state, the `agent-task`
> workflow, and operating principles. **Then** read this file and follow the
> session-start protocol below for spec_agents-specific context.

---

## Session-Start Protocol

When starting a new session on spec_agents, do these five things before
proposing or executing any work:

1. **Read [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md)** — snapshot of where things are right now (commit, tests, public surface, active task).
2. **Read [../planning/SYSTEM.md](../planning/SYSTEM.md) §11** — SA-* and XR-005 task definitions for this repo.
3. **Verify the build:** importable surface check (`python -c "import spec_agents"` should succeed); once SA-001 lands, `python -m pytest -q` should match the test count in CURRENT_STATE.md.
4. **Verify git is clean:** `git status --short` should be clean (or only show expected untracked files).
5. **Ask the operator which task to work on** — don't assume.

If you find drift between CURRENT_STATE.md and reality, **fix the doc first** before doing other work. CURRENT_STATE.md is the contract.

---

## Repo-specific notes

`spec_agents` is the foundation library extracted from `spectacular` on 2026-05-12.
Domain-agnostic agent + adapter primitives consumed by `spectacular`, `personal_os`,
and (eventually) `photo_archive`.

## Current state

Tagged `v0.1.0` (2026-05-20). See [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md)
for the live snapshot (commit, tests, pre-commit posture). Active backlog in
[../planning/SYSTEM.md](../planning/SYSTEM.md) — primarily SA-002 (critic),
SA-003 (verifiers), SA-004 (plan-then-act), gated behind the foundation pass.

## Public surface — do not break

- **Adapter ABC** (`spec_agents.ingestion.adapters.base.Adapter`)
- **Knowledge layer** (`spec_agents.agents.knowledge.lenses`, `.memory`)
- **DB helpers** (`spec_agents.storage`)
- **Structured logging** (`spec_agents.logging.setup`)
- **Pydantic message types** (`spec_agents.messages`)

**Consumers pin via git URL** (XR-005, 2026-05-20):

```toml
"spec-agents @ git+https://github.com/picnc6uy/spec_agents@v0.1.0",
```

For local dev, override the pin in the consumer venv:
`pip install -e ../spec_agents`. This is the standard pattern when iterating
on a kernel change before cutting a new tag.

Don't ship breaking changes to the public surface without (a) bumping
`pyproject.toml` version, (b) tagging the new release, (c) updating the pin
in `spectacular` and `personal_os`. Each surface change is now an explicit
version event, not implicit drift.

## Dependencies

Pinned in `pyproject.toml`: anthropic, requests, pydantic, sqlalchemy, structlog.
Dev: pytest, pytest-cov.
