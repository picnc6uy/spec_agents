# spec_agents — Current State Snapshot

This file is the **first thing** to read at the start of a new session.
It answers "where are we?" in 60 seconds. Keep it short. Update it when
material things change.

---

## As of 2026-05-28

**Master commit:** `792f116 chore: add agent-task contracts (.agent/) + CURRENT_STATE drift refresh`. Recent landings since 2026-05-23: `792f116` (agent-task contracts + drift refresh), `6fb4a29` (Gap 2 — SPRINTS.md backlog sketches), `d3058c5` (Gap 1 — drift-audit pre-commit hook installed), `2b401d3` (CURRENT_STATE discipline-sprint refresh to 2026-05-23). Kernel-freeze posture in effect; v2 sprint plan calls for spec_agents maintenance-only this cycle. **`spec-agents-lens-validator` ships imminently** (closes Move 1 of D-citations-files-pdf DECLINE): adds `LensLoader.validate()` + auto-warn in `__init__` + `ValidationIssue` dataclass.

**Tag:** `v0.6.0` (2026-05-20, SA-004 ships the two-call plan-then-act
orchestration — pure composition of two `critic.critique` calls;
library-mode at its purest). Consumers pin via
`spec-agents @ git+https://github.com/picnc6uy/spec_agents@v0.6.0`.
Bump version on any further public-surface change.

**Pushed to:** `picnc6uy/spec_agents` (private GitHub).

**Tests:** 67 passing in ~1.4s · ruff + ruff-format clean.
Surface coverage: imports, Adapter ABC contract enforcement, LensLoader
header-anchored extraction, AgentMessage falsifiability invariant,
`spec_agents.testing.db` (XR-009), `spec_agents.agents.critic.critique`
(SA-002), `spec_agents.eval.run_eval` + `aggregate_numeric` (XR-010),
`spec_agents.agents.verifiers` (SA-003), and
`spec_agents.eval.batch.submit_batch` + `wait_for_batch` +
`fetch_results` + `build_invoker` (round-trip through `run_eval` with
stubbed SDK; missing-result + errored-result paths) per XR-011.

**Pre-commit:** `ruff` (with `--fix`) · `ruff-format` · pre-commit-hooks
(trailing-whitespace, end-of-file-fixer, check-yaml, check-toml,
check-merge-conflict, large-files, private-key) · `detect-secrets`
v1.5.0 with seeded `.secrets.baseline`. Pyright runs in CI (XR-008),
not in the hook.

**CI:** canonical workflow per XR-008 (Python 3.12; pip install -e
`.[dev]` + pinned ruff/pyright/detect-secrets; ruff check + format;
pyright strict; detect-secrets-hook against baseline; pytest).

**Conventions:** [docs/CONVENTIONS.md](CONVENTIONS.md) declares the
standards expected of consumers and is mirrored into `spectacular` and
`personal_os` (XR-006 executed 2026-05-20).

---

## Public surface — do not break

- **Adapter ABC** (`spec_agents.ingestion.adapters.base.Adapter`)
- **Knowledge layer** (`spec_agents.knowledge.lenses`: `Lens`,
  `LensSection`, `LensLoader`, `ValidationIssue`). `LensLoader.__init__`
  eagerly validates all `(lens, section)` triples and emits
  `log.warning("knowledge.lens_validation_issue", ...)` per broken
  reference (`doc_missing` or `header_missing`); callers can also call
  `loader.validate() -> list[ValidationIssue]` directly. Warning-mode:
  never raises. (Added 2026-05-28, spec-agents-lens-validator,
  closes Move 1 of D-citations-files-pdf DECLINE.)
- **DB helpers** (`spec_agents.storage`)
- **Structured logging** (`spec_agents.logging`)
- **Pydantic message types** (`spec_agents.messages`: `AgentMessage`,
  `EnsembleResult`, `EvidenceItem`, `Direction`)
- **In-memory test fixture** (`spec_agents.testing.db`:
  `in_memory_engine`, `in_memory_session`) — XR-009
- **Critic primitive** (`spec_agents.agents.critic.critique`) — SA-002
- **Eval harness** (`spec_agents.eval`: `run_eval`, `aggregate_numeric`,
  `EvalRun`, `EvalResult`, `Invoker`, `Scorer`) — XR-010
- **Verifier helpers** (`spec_agents.agents.verifiers`: `verify`,
  `verify_schema`, `verify_evidence`, `VerifierIssue`,
  `VerificationResult`, `Verifier`) — SA-003
- **Batch-API wrapper** (`spec_agents.eval.batch`: `submit_batch`,
  `get_batch_status`, `wait_for_batch`, `fetch_results`, `build_invoker`,
  `BatchResult`) — XR-011
- **Plan-then-act orchestration**
  (`spec_agents.agents.plan_then_act.plan_then_act`,
  `PlanThenActResult`) — SA-004

Consumers pin via the git-URL pattern in their `pyproject.toml`
(XR-005). For local dev, override with `pip install -e ../spec_agents`.

## What Works End-to-End

Public surface imports cleanly; every covered primitive round-trips
through its documented contract in the smoke-test suite. The critic
primitive specifically is exercised against a stub Anthropic client —
live-API behavior is owned by consumers (spectacular's brief_critic
regression suite).

## What's Stubbed / Deferred

- **`spec_agents.consolidation`** — runtime "dream" / memory consolidation
  primitive named in the v2 charter. Waits for Brier baseline + critic.

## Active Sprint

⬜ Foundation pass closed (XR-001/3/5/6/8/9, SA-001, POS-001). Methodology
band has five shipped primitives so far: SA-002 (critic, v0.2.0), XR-010
(eval harness, v0.3.0), SA-003 (verifiers, v0.4.0), XR-011 (batch
wrapper, v0.5.0), **SA-004** (plan-then-act, v0.6.0). Library-mode
posture proven across critic call, harness loop, zero-token checks,
async fanout, and two-call orchestration.
Next-3 in execution order: **POS-003** (personal_os summary critic —
first SA-002 consumer outside spectacular), **SR-006** (few-shot lens
upgrade — needs operator-curated run_ids; deferred until then),
**T-033** (Claude vision pipeline for photo_archive — gated on D-4
execution).

## Known Issues / Cleanup Items

- `agent-task` workflow contracts live in `planning/agent-task/`, not
  mirrored into this repo's docs. Considered acceptable: that workflow
  is cross-repo, not spec_agents-specific.

## How To Resume Work

1. `cd c:/Users/ghendrick/spec_agents`
2. Read this file (you just did)
3. Read `AGENTS.md` for the session-start protocol
4. Drift check: `git log --oneline -1` should match the master commit
   line above; if not, fix this file first
5. `python -m pytest -q` should show 67 passing
6. Read `planning/SYSTEM.md` §11 for SA-* and XR-010 scope
7. `git status` should be clean
8. Ask the operator which task to work on

## How To Update This File

Edit it when:

- A task ships that changes commit / tests / public surface
- A new public symbol is added or removed (also: bump version, tag,
  update consumer pins)
- A new known issue is discovered or resolved

Commit the update with the change that caused it. The drift-audit lens
(`planning/agent-task/agent-templates/lenses/drift-audit.md`) catches
divergence at session start and task close.
