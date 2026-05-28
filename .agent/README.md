# `.agent` -- Repo-local agent task contracts

The contract between the human operator and any AI agent (Claude Code,
Continue, etc.) working in this repo. The folder structure makes the dev
loop explicit on disk instead of in chat memory.

## The loop

1. Operator runs `agent-task new <id> <type>` -- creates a git worktree
   on branch `agent/<id>`, scaffolds `tasks/<id>.md` from
   `task-template.md`.
2. Operator fills in the task spec (or has the agent help with a first
   draft, then reviews).
3. Agent works in the worktree. At session start it reads the lens file
   named in the task spec's `lens:` field.
4. Before declaring done, agent writes `verifications/<id>.md` from
   `verification-template.md`. Every box in the verification doc must be
   filled with real evidence -- not "looks good".
5. Operator runs `agent-task close <id>` -- the tool verifies the
   verification doc, runs the automated gates one more time, fast-forwards
   `main`, deletes the branch and worktree.

## Folders

- `tasks/` -- one file per task, `T-XXX.md`. Created from `task-template.md`.
- `verifications/` -- one file per completed task, `T-XXX.md`. Created from
  `verification-template.md`.
- `lenses/` -- role/type lenses. Loaded by the agent at session start based
  on the `lens:` field in the task spec.

## Lenses available

| Lens | When to use |
|---|---|
| `new-feature.md` | Adding behavior. Forces test-first discipline. |
| `refactor.md` | Restructuring without changing behavior. Test count preserved. |
| `bug-fix.md` | Reproduce-then-fix. Failing test before patch. |
| `security-review.md` | Audit pass over code that handles secrets, I/O, or user input. |
| `architecture-review.md` | Evaluate, not implement. Output is a written assessment. |

Add more lenses as patterns emerge. One lens per task type is a soft cap --
two if a task spans them (e.g. `refactor.md + security-review.md`).

## Why this exists

Without enforced templates, every task is reconstructed from chat history
and "done" means whatever the agent thought it meant at the time.
Templates make the contract explicit on disk and make verification a gate,
not an afterthought.

See also: the `agent-task` CLI tool (run `agent-task help`).
