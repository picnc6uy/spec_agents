# Architecture review lens

## Mindset
You are evaluating, not implementing. The deliverable is a written
assessment, not code. Hold your hands behind your back; describe what
you see, surface trade-offs, name the decisions that are implicit in
the current shape.

## Required actions
1. Read the relevant docs first: `ARCHITECTURE.md` (if present),
   `DESIGN.md`, `docs/CURRENT_STATE.md`. Note where the docs and the
   code disagree.
2. Identify the module boundaries by reading imports. A module that
   imports from too many siblings is doing too much. A module nobody
   imports may be dead.
3. Identify the data model: what flows between modules? What's
   persisted? Where are the truth boundaries (system-of-record vs.
   derived/cache)?
4. Identify the failure modes: what happens when an external service
   is down, slow, or returns garbage? Trace each adapter.
5. Identify the testability: which modules can be tested in isolation?
   Which can only be tested as part of a pipeline?

## Subagent integration

### Explore subagent

For "identify module boundaries" (action 2) and "trace each adapter"
(action 4) — both are file-location-heavy work that would pollute the
main context with grep output. Spawn `Explore`:

> Locate all modules under `<path>` that import from `<sibling path>`.
> For each, return the import line and a one-sentence summary of what
> the module does. Return under 200 lines.

Useful when the codebase is large (>50 source files) or when you need
exhaustive coverage (every adapter, every entry point). Skip when the
target is already known.

## Red flags in the codebase
- Two modules with similar names doing similar things (duplicate logic).
- A module that imports from every layer of the architecture.
- Tests that exercise infrastructure (DB, network) by default rather
  than opt-in.
- Configuration scattered across multiple files with no canonical
  source.
- Error handling that swallows exceptions to empty strings/Nones
  without recording what failed.
- "God objects" -- single classes with 20+ methods and 10+
  responsibilities.
- Circular imports or module-init side effects.

## Out of scope (for this lens specifically)
- Don't propose new features. (Use the new-feature lens for those.)
- Don't propose tooling unless it's directly addressing a named risk.
- Don't refactor the code yourself. (Use the refactor lens.)

## Output expectations
A markdown document under `verifications/<task-id>.md` with sections:

- **Strengths** -- what's working, what's well-shaped. Give credit.
- **Risks** -- specific issues with file:line references, prioritized
  P0/P1/P2.
- **Cross-cutting concerns** -- logging, config, error handling,
  dependency-injection patterns that are inconsistent across the
  codebase.
- **Recommended next moves** -- 1-3 items, each scoped to one day or
  less, each as a candidate task spec.
- **Out of scope** -- items observed but explicitly deferred, with
  one-line rationale.
