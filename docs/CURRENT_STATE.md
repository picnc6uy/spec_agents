# spec_agents — Current State Snapshot

This file is the **first thing** to read at the start of a new session.
It answers "where are we?" in 60 seconds. Keep it short. Update it when
material things change.

---

## As of 2026-05-28

**Master commit:** `usage-cost-fn: add spec_agents.usage — single-source pricing` (HEAD after ff-merge of the usage-cost-fn branch). Recent landings 2026-05-28: lens-validator (v0.7.0), conftest sys.path, version sync, pyright config fix (`strict = []`), Opus 4.8 docstring migration, and **usage-cost-fn (v0.8.0)**. Kernel-freeze posture remains; this `usage` add is an operator-approved freeze exception (single-source pricing function) per the 2026-05-28 comprehensive review Open Q3.

**Tag:** `v0.8.0` (2026-05-28, adds `spec_agents.usage`:
`model_cost_usd()` + `PRICING_USD_PER_MTOK` — single source of truth for
Anthropic token→USD cost across the stack). Prior: `v0.7.0`
(`LensLoader.validate()` + `ValidationIssue`). Consumers pin via
`spec-agents @ git+https://github.com/picnc6uy/spec_agents@v0.8.0`.
Bump version on any further public-surface change.

**Pushed to:** `picnc6uy/spec_agents` (private GitHub).

**Tests:** 73 passing in ~1.5s · ruff + ruff-format clean.
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
pyright (default mode — `strict = []`, not strict; corrected 2026-05-28
doc-honesty sweep); detect-secrets-hook against baseline; pytest).
`pyright==1.1.360` is now also pinned in the `dev` extra so a local
`.[dev]` reproduces CI's type-check (spec-agents-pyright-pin, Open Q5).

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
- **Usage pricing** (`spec_agents.usage`: `model_cost_usd`,
  `PRICING_USD_PER_MTOK`) — single source of truth for Anthropic
  token→USD cost. Pure function; raises `KeyError` on unknown model.
  (Added 2026-05-28, usage-cost-fn, v0.8.0.)

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
5. `python -m pytest -q` should show 73 passing
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
