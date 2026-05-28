# New feature lens

## Mindset
You are adding behavior. Every new code path must have a corresponding
test that exercises it. No exceptions: not "trivial config", not
"obviously correct", not "covered indirectly". If it's not tested, it
isn't done.

## Required actions
1. Write the test first or at the same time as the implementation. Tasks
   that add code without tests should be rejected at the verification gate.
2. Update the relevant `docs/CURRENT_STATE.md` to reflect what's now
   possible.
3. If the feature touches an external contract (API endpoint, database
   schema, config key, CLI flag), bump the relevant version and add a
   changelog entry.
4. Confidence assertions: prefer making the type system enforce
   invariants over runtime checks. If you need a runtime check, also add
   a test that verifies the failure path actually fails.

## Subagent integration

### Plan subagent (for non-trivial features)

If the feature touches multiple modules or introduces a new architectural
shape, spawn `Plan` before implementing:

> Designing implementation strategy for <feature>. Inputs: the task
> spec + current architecture summary. Return 1-3 strategy options with
> trade-offs, implementation order, files-to-touch list, risks. Under
> 600 words.

Skip for features that are clearly localized (one file, no API change,
no new dependencies).

### Explore subagent

For "where do I add this?" — find extension points, existing patterns
to mirror, public surface to extend:

> Find existing <similar pattern> in the repo. Return file:line + a
> short summary. Where would <new thing> naturally extend this?

## Red flags
- Tests added that only assert "no exception was raised".
- New optional parameters with mutable defaults (`def f(x=[]):`).
- `print()` statements left in (use `structlog` / the project's logger).
- `TODO` / `FIXME` comments in shipped code -- if it needs to be done,
  do it; if it doesn't, drop the marker.
- New imports of packages not in `pyproject.toml`.

## Sanity check before verification
```bash
# New tests should be visible in the count.
git stash; pytest -q --co | wc -l > /tmp/before
git stash pop
pytest -q --co | wc -l > /tmp/after
# /tmp/after should be larger than /tmp/before, by the number of new tests.
```

## Output expectations
In the verification doc:
- List every new test by name with a one-line description of what it covers.
- State the line coverage delta for the new module/function (target: >80% of new lines).
- Confirm the schema/version bump if one was warranted.
