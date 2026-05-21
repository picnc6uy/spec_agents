# AGENTS.md — spec_agents

> **Fresh session?** Start at [../planning/HANDOVER.md](../planning/HANDOVER.md) for the
> canonical session-start brief, then cross-reference architectural posture in
> [../planning/v2-charter.md](../planning/v2-charter.md) (the v2 charter —
> committed design rules, propagation tiers, library mode). **Then** read
> this file and follow the session-start protocol below for spec_agents-specific
> context.
>
> **Drift discipline:** at session start and task close, run the
> [drift-audit lens](../planning/agent-task/agent-templates/lenses/drift-audit.md)
> against the docs you're about to trust or just touched. Fix drift first; don't
> work over stale context.
>

---

## Discipline gate — READ BEFORE ANY CODE CHANGE

**Do not make code changes without an active task spec** at `.agent/tasks/<id>.md`. The spec is the contract; freestyle execution produces no audit trail and is the failure mode `planning/v1-state-report.md` was written to surface. Two cases:

1. **Spec exists** (operator ran `agent-task new <id> <type>`, branch is `agent/<id>`): proceed within the spec's `files.touched`, write `.agent/verifications/<id>.md` when done.
2. **No spec; operator gives ambiguous direction** ("go", "do option 1", "make X work"): your first response is *"what's the task spec? running `agent-task new` for that?"* — not direct execution.

The operator may explicitly waive (*"skip the spec for this drift fix"*). Trivial single-file doc edits and chore commits don't need a spec.

**Before complex inline work, match the task to available subagents.** `Plan` for planning tasks (the planning lens requires the spawn), `Explore` for file-location and reference searches (architecture-review / bug-fix / refactor lenses recommend it), `general-purpose` for multi-step research across the repo (security-review prefers it). Each lens names the subagent it expects — read the lens at session start and check before working inline. The default of "do not spawn subagents unless asked" is overridden by the lens's `Subagent integration` section.

A pre-commit hook on `agent/*` branches enforces this mechanically — commits without `.agent/tasks/<id>.md` are rejected. Bypass with `--no-verify` only when the operator has waived.

See `../planning/dev-env-handoff.md` ("Prompts are soft; protocols are hard") and `../planning/v1-state-report.md` for the rationale.

---

## Session-Start Protocol

When starting a new session on spec_agents, do these five things before
proposing or executing any work:

1. **Read [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md)** — snapshot of where things are right now (commit, tests, public surface, active task).
2. **Read [../planning/SYSTEM.md](../planning/SYSTEM.md) §11** — SA-* and XR-005 task definitions for this repo.
3. **Drift check** — quick scan of `CURRENT_STATE.md` master commit vs `git log --oneline -1` and decisions section vs `planning/HANDOVER.md`. If drift found, fix the doc *first*. See [drift-audit lens](../planning/agent-task/agent-templates/lenses/drift-audit.md).
4. **Verify the build:** importable surface check (`python -c "import spec_agents"` should succeed); `python -m pytest -q` should match the test count in CURRENT_STATE.md.
5. **Verify git is clean:** `git status --short` should be clean (or only show expected untracked files).
6. **Ask the operator which task to work on** — don't assume.

If you find drift between CURRENT_STATE.md and reality, **fix the doc first** before doing other work. CURRENT_STATE.md is the contract.

---

## Repo-specific notes

`spec_agents` is the foundation library extracted from `spectacular` on 2026-05-12.
Domain-agnostic agent + adapter primitives consumed by `spectacular`, `personal_os`,
and (eventually) `photo_archive` + `dictionary`.

**Library mode is committed** (v2 charter, 2026-05-20). The kernel does not
autonomously orchestrate — primitives are functions agents call. Don't propose
framework-mode shapes for SA-002 / SA-003 / SA-004 without operator-initiated
reopening of the posture question.

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
