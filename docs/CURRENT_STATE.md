# spec_agents — Current State Snapshot

This file is the **first thing** to read at the start of a new session.
It answers "where are we?" in 60 seconds. Keep it short. Update it when
material things change.

---

## As of 2026-06-08

**HEAD + test count:** machine-written in the `planning/START_HERE.md` stack-state
block (run `git log --oneline -1` and `pytest --collect-only -q` to confirm against
it). Reviewed 2026-06-08 (planning S3 doc-honesty sweep); content below current as of the v0.12.0 release.

**Release:** **v0.12.0 tagged + pushed** — bundles the `tui` kit (Rich + offline-HTML
+ Textual `record_browser` targets) and `secrets.get_secret()` (keyring-first, env
fallback) on top of v0.11.x (corpus-first caching hooks, `verify()` fail_severity
guard). v0.11.0 + v0.11.1 were also back-tagged today at their exact commits
(`b9d7503`, `39c5bb9`). `__init__.__version__` re-synced to pyproject (had lagged at
"0.10.0" since v0.10.1). Consumers pin via
`spec-agents @ git+https://github.com/picnc6uy/spec_agents@v0.12.0`; `textual` is an
optional extra (`spec-agents[textual]`) — the kit imports it lazily.
**Tests:** green (exact count in the `planning/START_HERE.md` stack-state block; `pytest --collect-only -q` for the precise figure).

---

## As of 2026-06-02

**Latest landing:** `spec_agents.tui` — a reusable, target-agnostic terminal-UI
kit. Declarative blocks (`View`, `Badge`/`Badges`, `BarRow`/`BarTable`, `Note`,
`Table`) are described once and rendered to either a Rich terminal view
(`render_rich`) or a self-contained OFFLINE HTML page (`render_html`, inline CSS
only — no `src=`/`<script>`/CDN). Operationalizes the house style in
`planning/terminal-output.md` (semantic tones good/warn/bad/neutral;
right-justified numbers; 28-cell unicode bars; shared utf-8 / non-legacy
Console). `rich` is imported lazily so importing the kit needs no extra deps.
First consumer: `planning/scripts/cost_reconcile.py` now builds its dashboard via
`build_view(report)` and delegates both `--tui` and `--html` to the kit (its 55
tests unchanged + green). **Tests:** 121 passing (103 prior + 18 new
`tests/test_tui.py`).

**Prior landing:** `verify-fail-severity-guard` (**v0.11.1**, bug-fix) — `verify()` now
validates `fail_severity` at entry and raises `ValueError` on an unknown threshold.
Previously a typo'd `fail_severity` ranked 99, so no real issue met it and verification
silently returned `passed=True` (a check that couldn't fail). Issue severities keep the
safe asymmetry (unknown ranks highest → fails). Signature unchanged. Found by the
code_review_swarm dogfood review of this repo.

**Prior landing:** `code-review-swarm` sprint A (**v0.11.0**) — two additive,
backward-compatible caching hooks so one large corpus can be cached **once and
read across many calls** (the cross-tier / shared-lens cases):

- `map_agent(..., cached_prefix_text=...)` — when given, the corpus becomes the
  sole *leading* cached block and `shared_system_text` trails it *uncached*, so a
  breadth pass and a confirm pass over the same corpus share one cache entry.
  Default `None` preserves the original single-cached-block behavior.
- `critique(..., lens_first=True)` — places the cached lens block *before* the
  rules block, so a synthesizer and its paired challenger (different rules, same
  corpus) reuse one cached lens. Default `False` preserves rules-first ordering.

Foundation for `planning/scripts/code_review_swarm.py` (sprint B; design:
`planning/architecture-reviews/2026-06-01-code-review-swarm-design.md`).
**Tests:** 103 passing · pinned ruff 0.8.4 check+format clean · pyright 1.1.360
strict clean. Bump version on any further public-surface change.

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
- **Critic primitive** (`spec_agents.agents.critic.critique`) — SA-002.
  `lens_first=True` (v0.11.0) flips to lens-before-rules for shared-lens caching.
- **Parallel map** (`spec_agents.agents.parallel.map_agent`, `MapResult`,
  `MapUsage`) — warm-then-fan-out fan-out with usage/churn rollup.
  `cached_prefix_text=...` (v0.11.0) puts a stable corpus in the sole leading
  cached block for cross-call reuse.
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
4. Drift check: compare `git log --oneline -1` against this repo's line in
   the generated stack-state block in `planning/START_HERE.md` (HEAD + test
   count are machine-written there). If this file's prose disagrees, trust
   git + the block and fix the prose.
5. `python -m pytest -q` should pass. Don't match a hand-typed count — the
   exact figure is `python -m pytest --collect-only -q | tail -1`, and the
   stack-state block carries the at-a-glance number.
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
