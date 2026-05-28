# Drift-audit lens

## Mindset

Docs drift the moment they stop matching reality. The system depends on
agents trusting `HANDOVER.md`, `SYSTEM.md`, per-repo `CURRENT_STATE.md`,
and memory entries as accurate. If those drift, every future session
starts from a lie and the methodology degrades quietly.

This lens is the routine — short, mechanical, non-judgmental — that
catches drift before it spreads. **It exists so the operator doesn't
have to police docs manually.** Run it at three checkpoints:

1. **Session start** — before proposing any work, scan for drift in the
   docs you're about to trust. If you find drift, fix the doc *first*,
   then do the work.
2. **Task close** — as part of every verification doc, confirm this task
   didn't leave any cross-repo doc stale.
3. **Weekly** — a deliberate full pass. Schedulable via `/loop` or
   `/schedule`.

## Required actions — the audit checklist

Run these checks. For each, note **OK** or **drift found → fix**.

### 1. Per-repo `CURRENT_STATE.md` vs git HEAD

For each canonical repo (`spec_agents`, `spectacular`, `personal_os`,
`photo_archive`):

- [ ] **Master commit line** matches `git log --oneline -1`. If not,
      update the commit SHA + short message.
- [ ] **Test count line** matches the latest test run (or is annotated
      as "not verified this session" honestly).
- [ ] **Pre-commit / CI posture** statements match the live config.
- [ ] **"What's stubbed / deferred" list** doesn't claim deferral for
      things that have already shipped, and doesn't omit deferrals that
      just got added.
- [ ] **"Recently landed" list** reflects work done since the file was
      last touched.

### 2. `planning/HANDOVER.md` vs reality

- [ ] **Last updated date** is within the last 14 days. If older, audit.
- [ ] **"What's already done — don't redo" list** matches actual state.
      Common drift: tasks listed as pending that are done; tasks listed
      as done with stale commit SHAs.
- [ ] **Decisions section** matches `planning/SYSTEM.md` §3 *and* the
      `decisions.md` memory entry. All three must agree on signed /
      pending status.
- [ ] **Current immediate task** points at a task that's actually staged,
      or says "no task staged" if none is.

### 3. `planning/START_HERE.md` vs reality

- [ ] **Project table "Next move" column** is current per repo.
- [ ] **Decisions list** matches HANDOVER + SYSTEM + memory.
- [ ] **"This week I will NOT" list** doesn't forbid things that are now
      explicitly allowed.

### 4. `planning/SYSTEM.md` vs reality

- [ ] **Decision sign-offs (D-1..D-6, XR-006)** match the memory's
      `decisions.md`.
- [ ] **Task status lines** (TODO / DONE / IN PROGRESS) match what's
      shipped. Common drift: tasks marked TODO that have shipped commits.
- [ ] **Parity table at §4** reflects current cross-repo capability
      state.

### 5. Memory entries (`~/.claude/projects/.../memory/`)

- [ ] **`decisions.md`** matches HANDOVER + SYSTEM. Single source of
      truth among the three.
- [ ] **`reference_v2_charter.md`** path still resolves
      (`planning/v2-charter.md`).
- [ ] **Status flags ("RESOLVED", "AWAITING SIGN-OFF", "DONE")** are
      consistent across `decisions.md`,
      `project_library_vs_framework.md`, and any `discogs_rotation.md` /
      similar.

### 6. Cross-doc reference integrity

- [ ] **Charter path** (`planning/v2-charter.md`) is the same string in
      every doc that references it (no leftover `v2 architecture/v2
      architecture - Unknown.md` references).
- [ ] **Repo names** match current state. `Spec_Report` references
      should be flagged as stale (D-1 still pending GitHub-side
      rename); `PhotoProject` references are stale (D-4 executed
      2026-05-20; canonical name is `photo_archive`). Live local repo
      at `C:/Users/ghendrick/photo_archive`; archived legacy local at
      `C:/Users/ghendrick/_archive/PhotoProject` per D-4 Phase 4
      (2026-05-21).

### 7. Expected absences

Beyond stale positive references, drift also surfaces as **artifacts
that should be absent but aren't**. The dual to the staleness check.
Run these:

- [ ] **Archived-repo old paths.** Directories that were moved to
      `_archive/` should NOT also exist at their old location. Known
      cases:
      - `C:/Users/ghendrick/PhotoProject/` (post D-4 Phase 4
        2026-05-21) — may linger as an empty shell if a process held a
        file lock at move time. Cosmetic if empty; investigate if
        files have re-appeared.
- [ ] **Closed agent worktrees.** `agent-task close` removes
      worktree directories. If `C:/Users/ghendrick/planning--<id>`
      exists for any `<id>` whose branch has been merged + deleted,
      it's a leftover shell. Check: `git -C planning worktree list`
      should NOT mention closed-task paths. If `Get-ChildItem
      C:/Users/ghendrick -Filter 'planning--*' -Directory` returns
      entries not in the worktree list, those are orphan shells.
- [ ] **Untracked artifacts matching now-gitignored patterns.**
      When a file pattern gets added to `.gitignore` (e.g.,
      `spectacular/.gitignore`'s `brief_*.json` rule), existing files
      on disk are merely no-longer-tracked. They should typically be
      deleted unless explicitly retained.
- [ ] **Stale agent branches.** Local branches `agent/<id>` whose
      worktrees have been removed but branches lingered (rare; `close`
      deletes both; check anyway).

**Triage rule when an expected absence is violated:**

1. **Cosmetic** — locked by another process, no files inside, will
   clear when the lock releases. Note in audit report; no fix
   required.
2. **Real** — something restored or recreated the absent artifact
   (e.g., a clone of the old PhotoProject repo back into the old
   path, or a new file matching a gitignored pattern). Investigate
   root cause. Fix at the source, not by deletion.
3. **Forgotten** — the artifact was supposed to be deleted but wasn't
   (e.g., post-close worktree shell still around). Operator + agent
   manually clean up; consider tooling (`agent-task close --force-
   cleanup`?) for repeat patterns.

The empty `PhotoProject/` shell post-2026-05-21 is the motivating
case for this section. As of the addition date, the shell is
cosmetic (locked by Continue.dev SQLite indices via VS Code). Audit
reports should record its expected absence with current status
("still locked" / "cleared" / "investigate") until the operator
manually removes it once the lock releases.

## Subagent integration

### Explore subagent (optional)

The drift-audit is usually fast enough to do inline — most checks are
single-file reads with `grep`. Spawn `Explore` only when:

- Scanning many cross-doc references across all repos for a specific
  stale string (e.g., "v2 architecture - Unknown" or old commit SHAs).
- Auditing memory entries that reference paths or commits that may no
  longer resolve.

> Find all references to `<pattern>` across `planning/` and the
> canonical-stack repos. Return file:line for each.

Most drift-audit work doesn't need delegation; the lens is itself
mostly a checklist. Delegating to a subagent obscures the discipline.

## Red flags

- A "Last updated" date older than 14 days on any of HANDOVER /
  START_HERE / a CURRENT_STATE.md.
- A decision marked pending in one doc and signed in another.
- A "done" claim with a commit SHA that doesn't exist in the repo.
- A "What's stubbed" entry for capability that just shipped.
- A path reference (charter, lens, anything in `planning/`) that doesn't
  resolve.

## Resolution rule

> **Fix the doc first, then continue the task.**

Drift discovered during session-start is not "context" — it's a bug in
the documentation layer. Fix it in the same commit as the work being
done, or in a `docs:` commit immediately before. Never leave drift in
place to "address later."

## Sanity check before verification

```bash
# Quick pass on the canonical docs:
grep -l "v2 architecture - Unknown\|D-1.*pending\|D-4.*pending\|D-6.*defer\|D-6.*pending" \
  C:/Users/ghendrick/planning/*.md \
  C:/Users/ghendrick/{spec_agents,spectacular,personal_os,photo_archive}/AGENTS.md \
  C:/Users/ghendrick/{spec_agents,spectacular,personal_os,photo_archive}/docs/CURRENT_STATE.md \
  2>/dev/null

# Master-commit drift per repo:
for r in spec_agents spectacular personal_os photo_archive; do
  echo "=== $r ==="
  echo "HEAD: $(cd /c/Users/ghendrick/$r && git log --oneline -1)"
  echo "CURRENT_STATE.md says:"
  grep -E "Master commit|Main commit" /c/Users/ghendrick/$r/docs/CURRENT_STATE.md | head -1
done
```

If either command turns up unexpected results, drift was found.

## Output expectations

If used inside a verification doc (Section: "Documentation drift"):

- [ ] Ran the checklist for the planning docs touched by this task.
- [ ] Ran the checklist for `CURRENT_STATE.md` in any repo touched.
- [ ] If drift was found: it was fixed in this commit / in a
      preceding `docs:` commit on the same branch.
- [ ] Memory entries that reference changed state have been updated (or
      a follow-up memory edit is queued and noted).

If used as a standalone audit task (recommended cadence: weekly), write
the findings into a short report at
`planning/drift-audits/YYYY-MM-DD.md` and link it from the HANDOVER's
"Last audit" line.

## Why this lens exists

Iterative development is the operator's stated style; the operator
should not need to police docs to stay aware of progress. This lens
encodes the awareness loop directly into the agent's session-start and
task-close discipline. Every commit becomes an opportunity to catch
drift; every session start becomes a chance to fix it before it
compounds.

The four-beat discipline at the dev meta-layer applies here too:
constrain (this checklist) → execute (scan) → validate (fix drift
in-commit) → gate forward (verification doc confirms).
