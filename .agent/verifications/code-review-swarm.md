---
task-id: code-review-swarm
verified: 2026-06-01
status: ready-to-merge
agent: claude-code
---

# Verification for code-review-swarm (sprint A — spec_agents foundation)

Two additive, backward-compatible caching hooks that let one large corpus be cached **once and
read across many calls**: `map_agent(..., cached_prefix_text=...)` and `critique(..., lens_first=True)`.
Foundation for sprint B (`planning/scripts/code_review_swarm.py`), design rev. 3 at
`planning/architecture-reviews/2026-06-01-code-review-swarm-design.md`.

Toolchain: a fresh `.venv` was built in the worktree with the **CI-pinned** tools
(`pip install -e ".[dev]" ruff==0.8.4 pyright==1.1.360 detect-secrets==1.5.0`) using Python 3.12
(`C:/Users/ghendrick/AppData/Local/Programs/Python/Python312/python.exe`). `.venv` is gitignored.

## Automated checks
- [x] `pytest -q` (full suite) — **103 passed** in ~1.5s (baseline 96 from spec-agents-parallel + **7 new**). No regressions.
- [x] `ruff check .` (**pinned 0.8.4**) — All checks passed. (Note: spectacular's venv ruff 0.15.13 reports
  UP046/UP047 on the pre-existing `MapResult`/`map_agent` generics — a newer-ruff artifact, not in the pinned set and not my code.)
- [x] `ruff format --check .` (0.8.4) — 39 files already formatted (my new test block was auto-formatted during the run).
- [x] `pyright` (**pinned 1.1.360, strict**) — **0 errors, 0 warnings** when pointed at the venv
  (`--pythonpath .venv/Scripts/python.exe`). Without that flag pyright resolves against the wrong interpreter
  and emits 18 `reportMissingImports` for third-party deps (sqlalchemy/anthropic/structlog/pydantic) that
  pytest proves are installed — environmental, pre-existing, none in my changed logic.
- [x] `git diff --name-only` matches `files.touched`: critic.py, parallel.py, test_critic.py, test_parallel.py,
  CURRENT_STATE.md, pyproject.toml + the task spec. Nothing else.

## Acceptance criteria
- [x] **map_agent gains `cached_prefix_text: str | None = None`** (keyword-only). `parallel.py` signature + docstring.
- [x] **None → byte-identical to legacy**: `system == [{"type":"text","text": shared_system_text, "cache_control":{"type":"ephemeral"}}]`.
  Evidence: `test_no_cached_prefix_is_byte_identical_to_legacy_single_block`.
- [x] **Provided → corpus-first, preamble uncached**: `system == [cached_block(corpus), {"type":"text","text": preamble}]`,
  cache_control ONLY on block[0]. Evidence: `test_cached_prefix_text_puts_corpus_first_and_preamble_uncached`.
- [x] **critique gains `lens_first: bool = False`** (keyword-only). `critic.py` signature + docstring.
- [x] **False → ordering unchanged** `[rules, (cached) lens]`. Evidence: `test_critique_default_order_is_rules_then_lens`
  + all 7 pre-existing critic tests still green.
- [x] **True + lens → `[(cached) lens, rules]`**. Evidence: `test_critique_lens_first_puts_cached_lens_before_rules`.
- [x] **Cross-tier invariant**: identical corpus + different preamble → byte-identical leading cached block.
  Evidence: `test_cached_prefix_text_corpus_block_identical_across_differing_preambles`.
- [x] **Duo shared-lens invariant**: lens_first + identical lens + different rules → byte-identical leading block.
  Evidence: `test_critique_lens_first_shares_one_lens_block_across_differing_rules`.
- [x] **Both params additive/keyword-only; every existing test passes unchanged** — 96 prior all green within the 103.
- [x] **Test count strictly increases** (96 → 103); ruff + pyright clean.
- [x] **CURRENT_STATE.md updated; version 0.10.0 → 0.11.0**. (No CHANGELOG.md in repo — convention is
  CURRENT_STATE + version bump + commit message; spec amended to reflect this.)
- [x] `lens_first` is a **no-op without lens_content**: `test_critique_lens_first_noop_without_lens_content`.

## Out-of-scope confirmation
- [x] No `files.must-not-touch` modified: `git diff` shows `caching.py`, `usage.py`, `eval/` untouched.
- [x] **MapResult/MapUsage dataclass shapes unchanged** — `git diff parallel.py` contains no `@dataclass`/`class Map*` lines.
- [x] No consumer script written here — that is sprint B in the `planning` repo.

## Things I deliberately did not do
- Did not build `code_review_swarm.py` (sprint B; blocked on this merging + the planning tree's stray
  untracked `photo_archive.txt` being resolved by the operator).
- Did not tag `v0.11.0` or bump consumer pins — operator release step.
- Did not reconcile CURRENT_STATE's older lag (it claimed v0.8.0/73 tests while pyproject was 0.10.0); added
  a current 2026-06-01 entry and fixed the live "should show N passing" instruction (73 → 103). Deeper
  back-reconciliation is out of this sprint's scope; flagged for the drift-audit lens.

## Risks for human reviewer
- The cross-tier cache win only materializes if the **caller** passes the same corpus as `cached_prefix_text`
  across tiers AND keeps the run contiguous (5-min TTL). The primitive enables it; sprint B must use it correctly.
- `lens_first` reorders system blocks — any caller that (wrongly) assumed `system[0]` is always the rules block
  would be affected, but the default is False so no existing caller changes behavior.

## Documentation drift (per the drift-audit lens)
- [x] `docs/CURRENT_STATE.md` updated (new 2026-06-01 entry, public-surface bullets for map_agent + critique, test count).
- [x] Cross-repo: the design doc (`planning/architecture-reviews/2026-06-01-code-review-swarm-design.md`) already
  describes these two changes as the required spec_agents additions; now implemented. No HANDOVER/SYSTEM status line claims this yet.
- [x] No memory entry references these symbols.
- [x] Path references resolve (design doc path checked).

## Diff summary
- 6 files changed, +207 / -12. parallel.py + critic.py: one kwarg + branch + docstring each. 7 new tests
  (3 parallel, 4 critic). CURRENT_STATE entry + surface bullets. Version 0.10.0 → 0.11.0.

## Verdict
Ready to merge.
