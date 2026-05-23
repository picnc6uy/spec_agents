# spec_agents — Sprint Plan

The forward-looking plan, with explicit acceptance criteria per sprint and a
status indicator on each. **Update the status line as work lands** so a fresh
session can see at a glance what's next.

Cross-repo cycle plan lives at
[planning/sprints/2026-05-23-next-cycle-plan.md](../../planning/sprints/2026-05-23-next-cycle-plan.md).
This per-repo file inherits the rules + adds spec_agents-specific guidance.

## Discipline Rules

1. **Kernel freeze posture (v2 charter committed).** No new primitives in
   spec_agents without explicit operator approval. The 5 primitives at v0.6.0
   (`critic`, `verifiers`, `plan_then_act`, `eval`, `batch`) are the surface.
2. **Each sprint ≤ 1 day of focused work.** If it grows past that, split it.
3. **Every sprint ends green** — `pytest -q` clean, ruff clean, pyright
   strict clean, commit pushed.
4. **No primitive ships without a real consumer.** If `personal_os`,
   `spectacular`, `photo_archive`, or a future canonical-stack repo isn't
   the use case, defer.
5. **API surface change → version bump.** Patch for additive, minor for
   refactors, never break consumers without operator approval.
6. **Consumers pinned via git URL** (`spec-agents @ git+...@vX.Y.Z`); use
   `scripts/bump_consumers.py` for cross-repo pin bumps.

---

## Current cycle posture (as of 2026-05-23)

**Kernel freeze continues.** Per the [cross-stack architect review 03](../../planning/architecture-reviews/2026-05-23-cross-stack-architect-review-03.md),
spec_agents has 3 of 5 primitives with real consumers
(`eval.batch`, `critic`, `testing.db`) and 2 that are nominal
(`plan_then_act`, `verifiers`). No consumer is currently asking for
new primitives. **No sprint this cycle.**

The next candidate primitive — `spec_agents.consolidation` (runtime dreaming
equivalent of the Auto Dream Skill) — waits for a Brier baseline per v2
charter. Baseline doesn't exist yet; no urgency.

---

## Sprints completed (history)

| Sprint | Title | Tag | Status |
|---|---|---|---|
| XR-008 | Pyright strict + CI canonicalization | — | ✅ |
| XR-009 | `spec_agents.testing.db` primitive | — | ✅ |
| XR-010 | `spec_agents.eval.run_eval` + aggregators | — | ✅ |
| XR-011 | `spec_agents.eval.batch` (Anthropic Batch API wrapper) | — | ✅ |
| SA-002 | `spec_agents.agents.critic` | — | ✅ |
| SA-003 | `spec_agents.agents.verifiers` | — | ✅ |
| SA-004 | `spec_agents.agents.plan_then_act` | `v0.6.0` (2026-05-20) | ✅ |
| S1.E2 | CI Node 24 migration (FM-1) | — | ✅ 2026-05-21 |
| S1.E4 | AGENTS.md subagent tool-match guidance | — | ✅ 2026-05-21 |
| S1.E5 | drift-audit fix on CURRENT_STATE | — | ✅ 2026-05-21 |

---

## Active backlog (Not Sequenced)

Each item is a sketch, not a scheduled sprint. Each requires explicit
operator approval to open (kernel-freeze gate).

### `consolidation` primitive (deferred until Brier baseline lands)

Runtime dreaming equivalent of Anthropic's Auto Dream Skill. Per v2
charter, runtime dreaming waits for:
1. A Brier baseline (currently does not exist anywhere in the stack).
2. The critic primitive (✅ shipped as `SA-002`).

When both conditions are met, this becomes a candidate sprint.

### Cache primitive (if a sibling app demands it)

Surfaced as a v2 lesson from photo_archive's first full-domain delivery
(see [photo_archive arc review 02](../../planning/architecture-reviews/2026-05-23-photo-archive-arc-review-02.md) §"Lessons to apply to v2").
photo_archive's 3 ad-hoc cache implementations (`DiscogsCache`,
`DahrCache`, `MbCache`) would benefit from a `spec_agents.cache`
filesystem-or-SQLite primitive.

**Trigger:** the second domain app (dictionary, or photo_archive's
refactor sprint S-pa-3) demands it. Not yet.

### Matrix-eval primitive (if T-033b shape gets canonized)

Per cross-stack review 03 Gap 3 + photo_archive arc review 02 P0, the
matrix-cross-product shape `parse_matrix.py` was the actual-execution
shape that bypassed `run_eval`. A `spec_agents.eval.matrix(invokers,
scorers, items)` primitive would canonize that pattern.

**Trigger:** operator decides to act on Gap 3 (cross-stack review 03).

---

## Maintenance work (does not require a sprint)

These are PRs that may land outside sprint cadence:

- **Patch-version bumps** for additive surface (e.g., new eval aggregator).
- **Drift-audit-induced doc refreshes** (CURRENT_STATE.md staleness fix —
  now enforced via pre-commit drift-audit hook landed 2026-05-23).
- **CI / pre-commit / pre-commit hook version pins** if security-driven.
- **Documentation clarifications** that don't change behavior.

For each, follow the [drift-audit lens](../../planning/agent-task/agent-templates/lenses/drift-audit.md) at commit time.

---

## How To Use This Document

**At the start of a session:** read this file + [docs/CURRENT_STATE.md](CURRENT_STATE.md). For spec_agents, normally the answer is "kernel freeze; no active sprint." Confirm with the operator before opening anything.

**During an approved sprint:** create `agent/<id>` branch + `.agent/tasks/<id>.md` spec; flip the relevant backlog item to 🟡 in progress here.

**At sprint close:** flip to ✅ done, update CURRENT_STATE.md, ff-merge to master, tag if version bump warranted.

**Never:** ship a new primitive without a real consumer. Library-mode discipline.

---

*See [planning/sprints/2026-05-23-next-cycle-plan.md](../../planning/sprints/2026-05-23-next-cycle-plan.md) for the cross-repo cycle plan.*
