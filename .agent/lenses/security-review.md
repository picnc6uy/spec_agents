# Security review lens

## Mindset
You are looking at code that handles secrets, network I/O, file paths,
or user input -- three places we get bitten. Trust nothing; document
every trust boundary explicitly. The output of this lens is a written
assessment with file:line citations, not code changes.

## Required actions
1. Identify every entry point (HTTP handlers, CLI args, file readers,
   environment-variable reads, message-queue consumers).
2. For each entry point, trace what is trusted vs. validated. Cite line
   numbers.
3. Check secret handling: never logged at any level, never written to
   disk unencrypted, never accepted from a non-`.env` source in shipped
   code. Search the diff for KEY/TOKEN/SECRET in print/log/repr contexts.
4. Check path handling: use `Path(...).resolve().is_relative_to(root.resolve())`,
   never `str(p).startswith(str(root))`. Reject symlinks that escape
   the workspace root.
5. Check subprocess calls: `shell=False`, `shlex.split(...)` for argv,
   allow-list of full commands (not prefix matches), timeout set, no
   string concatenation with anything that came from user input.
6. Check dependencies: pin versions, run `pip-audit` if available,
   document any package with known CVEs (with mitigations).
7. Check error handling: exceptions that include sensitive context
   (paths, credentials, request bodies) must not be re-raised verbatim
   to the user.

## Subagent integration

### general-purpose subagent

Security audits frequently trace multi-step paths (input → validator →
storage → output). Doing this inline pollutes the main context with
greps and excerpts. Spawn `general-purpose`:

> Trace handling of <input type> from entry point to output. List
> every transformation, every validation, every storage step. Return
> a numbered chain with file:line for each step. Under 100 lines.

Useful for end-to-end traces (the heart of any non-trivial audit).
Skip for spot checks (single-function review where the context fits
in one read).

## Red flags
- `subprocess.run(command, shell=True)`
- Any `startswith()` for path validation
- Logging code where the value is included when the key contains KEY,
  TOKEN, or SECRET (case-insensitive)
- Hardcoded credentials anywhere, including tests (use fixtures or
  recorded cassettes)
- `pickle.loads`, `eval`, `exec` with anything that isn't a literal
- HTTP without `https://` or with `verify=False`
- SQL string concatenation (use parameterized queries)
- File writes to paths derived from user input without normalization

## Sanity check before verification
```bash
# Quick automated probes.
detect-secrets scan
bandit -r src/                  # if available
pip-audit                        # if available
git grep -nE 'shell\s*=\s*True'
git grep -nE 'verify\s*=\s*False'
git grep -nE 'startswith\(.*root'
```

## Output expectations
The verification doc should include:
- **Findings table:** severity (Critical/High/Medium/Low), file:line,
  short description, recommended fix.
- **Trust boundaries:** a list of every external input and what
  validates it.
- **Items intentionally not in scope:** to prevent scope creep, name
  what you didn't review and why.
