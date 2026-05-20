# spec_agents — Current State Snapshot

This file is the **first thing** to read at the start of a new session.
It answers "where are we?" in 60 seconds. Keep it short. Update it when
material things change.

---

## As of 2026-05-20

**Master commit:** SA-003 verifier helpers (see latest commit message).

**Tag:** `v0.4.0` (2026-05-20, SA-003 ships verifier helpers — third
methodology-band primitive: pure-function checks that cost zero tokens).
Consumers pin via
`spec-agents @ git+https://github.com/picnc6uy/spec_agents@v0.4.0`.
Bump version on any further public-surface change.

**Pushed to:** `picnc6uy/spec_agents` (private GitHub).

**Tests:** 47 passing in ~1.3s · ruff + ruff-format clean.
Surface coverage: imports, Adapter ABC contract enforcement, LensLoader
header-anchored extraction, AgentMessage falsifiability invariant,
`spec_agents.testing.db` (XR-009), `spec_agents.agents.critic.critique`
(SA-002), `spec_agents.eval.run_eval` + `aggregate_numeric` (XR-010),
and `spec_agents.agents.verifiers.verify` + `verify_schema` +
`verify_evidence` (severity ranking, rule-crash containment, business-
rule + citation-resolution scenarios) per SA-003.

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
  `LensSection`, `LensLoader`)
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

Consumers pin via the git-URL pattern in their `pyproject.toml`
(XR-005). For local dev, override with `pip install -e ../spec_agents`.

## What Works End-to-End

Public surface imports cleanly; every covered primitive round-trips
through its documented contract in the smoke-test suite. The critic
primitive specifically is exercised against a stub Anthropic client —
live-API behavior is owned by consumers (spectacular's brief_critic
regression suite).

## What's Stubbed / Deferred

- **`spec_agents.agents.plan_then_act`** — SA-004 (two-call orchestration
  for structured decisions). Queued; awaits a real consumer (photo_archive
  match decisions per the brief).
- **Batch API integration in eval** — XR-011 (50% discount, overnight
  turnaround on 100s of historical runs). Gated on XR-010 having a real
  consumer; the kernel's `Invoker` callable already accepts any shape, so
  XR-011 wraps without changing the surface.
- **`spec_agents.consolidation`** — runtime "dream" / memory consolidation
  primitive named in the v2 charter. Waits for Brier baseline + critic.

## Active Sprint

⬜ Foundation pass closed (XR-001/3/5/6/8/9, SA-001, POS-001). Methodology
band in progress: **SA-002 shipped 2026-05-20** (critic primitive,
v0.2.0); **XR-010 shipped 2026-05-20** (eval harness, v0.3.0); **SA-003
shipped 2026-05-20** (verifier helpers, v0.4.0). Three matched
library-mode primitives, all consumed via plain Python callables — the
v2 charter's library-mode commitment in working form.
Next-3 in execution order: **SR-006** (few-shot upgrade — cheap,
parallelizable; consumer-only, no kernel work), **XR-011** (Batch API
integration), **SA-004** (plan-then-act).

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
5. `python -m pytest -q` should show 23 passing
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
