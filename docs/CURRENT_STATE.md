# spec_agents — Current State Snapshot

This file is the **first thing** to read at the start of a new session.
It answers "where are we?" in 60 seconds. Keep it short. Update it when
material things change.

---

## As of 2026-05-20

**Master commit:** SA-001 pass (see latest commit message).

**Tag:** `v0.1.0` (2026-05-20, D-5 signed; XR-005 closed). Consumers
pin via `spec-agents @ git+https://github.com/picnc6uy/spec_agents@v0.1.0`
in their pyproject.toml.

**Pushed to:** `picnc6uy/spec_agents` (private GitHub).

**Tests:** 16 passing in ~0.4s · ruff + ruff-format clean.
Surface coverage: imports, Adapter ABC contract enforcement, LensLoader
header-anchored extraction, AgentMessage falsifiability invariant,
`spec_agents.testing.db` (in-memory SQLite + schema_init hooks) per
XR-009.

**Pre-commit:** `ruff` (with `--fix`) · `ruff-format` · pre-commit-hooks
(trailing-whitespace, end-of-file-fixer, check-yaml, check-toml,
check-merge-conflict, large-files, private-key) · `detect-secrets`
v1.5.0 with seeded `.secrets.baseline`. Pyright runs in CI (XR-008),
not in the hook.

**Conventions:** [docs/CONVENTIONS.md](CONVENTIONS.md) declares the
standards expected of consumers (Python ≥3.12, ruff/pyright config,
Pydantic v2, SQLAlchemy 2.0+, structlog, Adapter pattern, lens pattern,
no live calls in unit tests, secrets via `.env`).

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

Public surface imports cleanly; the four covered primitives
(Adapter ABC, LensLoader, AgentMessage, RawMetricIn) round-trip through
their documented contracts in the smoke-test suite.

## What's Stubbed / Deferred

- **CI** — XR-008 will add the canonical workflow (will include pyright
  strict, currently only enforced via local `pyright .`).
- **`spec_agents.agents.critic`, `.verifiers`, plan-then-act helper** —
  SA-002 / SA-003 / SA-004 (queued behind foundation pass).
- **Tag + git-URL pin** — XR-005, gated on D-5.

## Active Sprint

⬜ Foundation pass per `planning/SYSTEM.md` 2026-05-20 reframe.
SA-001 shipped 2026-05-20. Next task in execution order: **XR-005**
(tag v0.1.0 + pin via git URL), gated on operator sign-off of D-5.

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
