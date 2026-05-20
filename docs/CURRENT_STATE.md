# spec_agents — Current State Snapshot

This file is the **first thing** to read at the start of a new session.
It answers "where are we?" in 60 seconds. Keep it short. Update it when
material things change.

---

## As of 2026-05-20

**Master commit:** `6e093f0` (XR-001: detect-secrets pre-commit hook)

**Tag:** none yet — v0.1.0 is the target (XR-005, gated on D-5).

**Pushed to:** `picnc6uy/spec_agents` (private GitHub).

**Tests:** none yet — SA-001 includes the first smoke tests (importable
surface check; instantiate Adapter ABC subclass; load a lens; instantiate
engine). Until then, "working" means the public surface imports without
error.

**Pre-commit:** `detect-secrets` v1.5.0 with seeded `.secrets.baseline`
(XR-001). Ruff + smoke tests arrive with SA-001.

---

## Public surface — do not break

- **Adapter ABC** (`spec_agents.ingestion.adapters.base.Adapter`)
- **Knowledge layer** (`spec_agents.agents.knowledge.lenses`, `.memory`)
- **DB helpers** (`spec_agents.storage`)
- **Structured logging** (`spec_agents.logging.setup`)
- **Pydantic message types** (`spec_agents.messages`)

Consumers install editable from a sibling clone
(`pip install -e ../spec_agents`) until v0.1.0 is tagged and a git-URL
pin replaces the editable install in `spectacular` and `personal_os`
pyproject.toml (XR-005, gated on D-5).

## What Works End-to-End

The public surface is importable as documented in CLAUDE.md. No
end-to-end behavior is verified yet — that's SA-001.

## What's Stubbed / Deferred

- **`docs/`** — only this file and a future `docs/CONVENTIONS.md` (SA-001).
- **CI** — XR-008 will add the canonical workflow.
- **`spec_agents.testing` shared fixture module** — XR-009.
- **`spec_agents.agents.critic`, `.verifiers`, plan-then-act helper** —
  SA-002 / SA-003 / SA-004 (queued behind foundation pass).
- **Tag + git-URL pin** — XR-005, gated on D-5.

## Active Sprint

⬜ **None.** Foundation pass in progress per `planning/SYSTEM.md`
2026-05-20 reframe. Next task in execution order for this repo: **SA-001**
(pre-commit ruff + CURRENT_STATE.md + smoke tests + CONVENTIONS.md).

## Known Issues / Cleanup Items

- No `pyproject.toml` polish beyond the initial extraction.
- No CI yet — XR-008.
- `agent-task` workflow contracts live in `planning/agent-task/`, not yet
  mirrored into this repo's docs.

## How To Resume Work

1. `cd c:/Users/ghendrick/spec_agents`
2. Read this file (you just did)
3. Read `planning/SYSTEM.md` §11 for SA-001 / XR-005 scope
4. Confirm: `git log --oneline -3` matches the master commit above
5. Confirm: `git status` is clean
6. Ask the operator which task to work on

## How To Update This File

Edit it when:

- A task ships that changes commit / tests / surface
- A new public symbol is added or removed
- A new known issue is discovered or resolved

Commit the update with the change that caused it. Never let this file
drift from reality — its whole job is to be accurate at-a-glance.
