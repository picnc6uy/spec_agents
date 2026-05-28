# Bug fix lens

## Mindset
First write a test that reproduces the bug -- a test that fails on
current code. Then fix the bug so the test passes. The test is what
makes this commit permanent. Without it, the bug returns the next time
someone refactors the area.

## Required actions
1. **Reproduce first.** Add a failing test under `tests/` that exercises
   the exact bug. The test name should describe the bug, e.g.
   `test_normalize_catalog_strips_whitespace_not_just_dashes`.
2. Commit the failing test by itself if it helps document the bug.
3. Fix the bug with the smallest change that makes the test pass.
4. Verify all OTHER tests still pass -- fixing one bug must not break
   five others.
5. Note in the verification doc whether the bug was caught by an
   existing test suite gap, and whether a coverage rule should be added
   to prevent similar gaps.

## Subagent integration

### Explore subagent

Before patching, use `Explore` to find related code paths and prior
occurrences of the bug pattern:

> Find all places in the repo that <call X / handle Y / parse Z>.
> Return file:line + a 2-line excerpt for each. Under 50 results.

Useful when the bug might exist in multiple places (parsing logic,
shared utility, near-duplicate functions) and a one-spot patch would
leave duplicates intact. Skip for obviously-localized bugs.

## Red flags
- Fixing without a test.
- "While I was in here" changes -- those go in a separate task.
- Modifying the broken function's signature (that's a refactor + bug fix
  combined -- split it into two tasks).
- Comments that excuse rather than explain ("// hack: not sure why").

## Sanity check before verification
```bash
# The new test should fail on main and pass on the branch.
git stash && pytest path/to/test_file.py -k <new_test_name> && git stash pop
pytest path/to/test_file.py -k <new_test_name>
```

Expected:
- First invocation: the new test fails (or doesn't exist yet on main).
- After `git stash pop`: the test passes.

## Output expectations
In the verification doc:
- Quote the failing assertion message from the reproduction test on main.
- Quote the passing output after the fix.
- State whether the bug was a regression, a longstanding issue, or
  exposed by a new code path.
- Recommend one preventative measure (a coverage rule, a type tightening,
  a removed footgun) -- not as part of this task, but for the backlog.
