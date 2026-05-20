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

One `init` commit (`8dd5bc5`). No `docs/`, no tests, no CI, no pre-commit, no tag.
See [../planning/SYSTEM.md](../planning/SYSTEM.md) tasks SA-001 (pre-commit +
CURRENT_STATE.md + smoke tests) and XR-005 (tag v0.1.0 + git-URL pin) for the
next things to land.

## Public surface — do not break

- **Adapter ABC** (`spec_agents.ingestion.adapters.base.Adapter`)
- **Knowledge layer** (`spec_agents.agents.knowledge.lenses`, `.memory`)
- **DB helpers** (`spec_agents.storage`)
- **Structured logging** (`spec_agents.logging.setup`)
- **Pydantic message types** (`spec_agents.messages`)

Consumers install editable from a sibling clone (`pip install -e ../spec_agents`)
until v0.1.0 is tagged and a git-URL pin replaces the editable install in
`spectacular` and `personal_os` pyproject.toml. Don't ship breaking changes to the
public surface without coordinating the version bump in both consumers.

## Dependencies

Pinned in `pyproject.toml`: anthropic, requests, pydantic, sqlalchemy, structlog.
Dev: pytest, pytest-cov.
