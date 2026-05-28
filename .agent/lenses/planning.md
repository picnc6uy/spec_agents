# Planning lens

## Mindset
You are deciding what to build, not what's there. The deliverable is a
written plan, not code. Hold your hands behind your back; describe what
to do, what NOT to do, and what each costs. Acknowledge the cost of
each proposed item AND the cost of leaving it out — both have weight.

Prune ruthlessly. A plan that tries to ship everything is not a plan;
it's a wishlist. The methodology rewards a coherent core executed
slowly, not an exhaustive backlog.

## Required actions
1. **Read the state first.** `planning/HANDOVER.md`, `planning/SYSTEM.md`,
   `planning/v1-state-report.md` (if present), and each in-scope repo's
   `docs/CURRENT_STATE.md`. Note drift between what's planned and what
   exists.
2. **Identify forced moves.** Deadlines, blockers, dependencies, things
   that decay if not done (e.g., the GitHub Actions Node 20 → 24
   deadline). Forced moves come first in any plan; ignoring them is
   accepting a future surprise.
3. **Identify high-leverage moves.** What single item, if shipped,
   unlocks the most downstream work or proves the most methodology
   claim? Cite v1-state-report or operator-stated goals.
4. **Identify methodology-validation opportunities.** For each proposed
   item, ask: what unproven claim about the methodology does shipping
   this close? Items that prove a claim outrank items that just extend
   capability.
5. **Acknowledge cost honestly.** Per item: rough time, context-window
   cost, blast radius, irreversibility. The cost of NOT doing it goes
   in too.
6. **Define done.** Each plan item gets a written success criterion —
   how will we know it's shipped, not just attempted?
7. **Spawn the `Plan` subagent for independent review** of your draft
   before writing the verification doc. See "Subagent integration"
   below for the briefing template and integration discipline.

## Subagent integration

### Plan subagent (required for non-trivial plans)

After drafting the plan and **before** writing the verification doc,
send the draft to the `Plan` subagent for independent architectural
review. Plan has no shared context with you — that's the point. It
catches naive priority orders, missed forced moves, and glossed-over
engineering complexity.

**Briefing template:**

> Reviewing a draft multi-repo development plan authored against
> `planning/agent-task/agent-templates/lenses/planning.md`. Inputs
> below. Return findings on: naive priorities, missed forced moves,
> scope mis-classification (in vs. out), methodology-validation gaps,
> per-item cost realism. Under 800 words. Direct, calibrated, willing
> to push back.
>
> **Task spec:** `<paste contents of .agent/tasks/<id>.md>`
> **Planning lens:** `<paste this lens file>`
> **Draft plan:** `<paste contents of the draft verification doc>`

**Integrate findings:** read Plan's response in full before changing
the draft. Decide which findings to incorporate; record disagreements
you reject in the verification doc's `Notes` section so the operator
sees both sides. Plan's output is advisory, not authoritative — the
lens and your judgment as executing agent govern final shape.

**When NOT to spawn `Plan`:**
- Trivial single-repo plans (1-2 items, no cross-cutting).
- Operator has already named the priority order in the briefing
  (don't second-guess explicit operator direction).
- Iterating on an already-approved plan (Plan reviews drafts, not
  revisions).

## Red flags
- A plan with no "out of scope" section. Pruning isn't optional.
- Items driven by what's interesting rather than what's leverage.
- "Refactor everything" or "type-hint everything" as a plan item — too
  big to be done, too vague to be measured.
- Plans that assume infinite operator attention. Calibrate to the
  actual operator bandwidth (1.5 contributors).
- Items without a definition-of-done.
- Items that depend on operator decisions not yet made; flag those as
  decision-gated, don't try to plan past them.
- Plans that ignore methodology validation entirely (just operational).
- Plans that ignore operational work entirely (just methodology).

## Out of scope (for this lens specifically)
- Don't implement anything. This is a plan, not code.
- Don't decide things the operator needs to decide; surface the
  decisions and propose recommendations, but flag what needs sign-off.
- Don't generate exhaustive backlogs. ~3-7 items per project is a plan;
  20 items is a list.
- Don't pick the operator's product direction; if the operator hasn't
  named what "success" looks like for a repo, ask before planning.

## Output expectations
A markdown document at `.agent/verifications/<task-id>.md` with sections:

- **Scope** — which repos this plan covers, what time horizon, what
  altitude (operational / strategic / methodology / mix).
- **Forced moves** — must-do items with their deadlines or decay
  conditions.
- **Per-repo plan** — for each in-scope repo: ~3-7 items, each with
  cost / leverage / definition-of-done. Order matters; the operator
  reads top-down.
- **Cross-cutting initiatives** — items that span repos (e.g., closing
  the eval loop, trying the Skills tier). Same shape as per-repo items.
- **Out of scope** — what we explicitly chose NOT to do, and why. This
  section is mandatory; if it's empty, the planning failed.
- **Decision-gated** — items that depend on the operator deciding
  something. Frame each as a question with a recommendation.
- **Methodology validation** — which unproven claims this plan would
  close if executed, mapped to specific items.

## How this lens differs from architecture-review
- architecture-review evaluates what exists; planning decides what to
  do next. Output of architecture-review is `risks/strengths`; output
  of planning is `forced moves / per-repo plan / out of scope`.
- architecture-review reads the code deeply; planning reads the state
  docs deeply and trusts the architecture work has been done.
- architecture-review can be done in one repo; planning is usually
  cross-repo and benefits from running in `planning/`.
