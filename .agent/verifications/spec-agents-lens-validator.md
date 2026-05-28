---
task-id: spec-agents-lens-validator
verified: 2026-05-28
status: ready-to-merge
agent: claude-code
---

# Verification for spec-agents-lens-validator

## Automated checks

- [x] `pytest -q` — **67 passed in 1.34s** (63 baseline + 4 new). Command:
  `PYTHONPATH=src python -m pytest -q`. PYTHONPATH set because spec_agents
  has no `tests/conftest.py` to inject `src/` (a known gap — see
  "Things I deliberately did not do").
- [x] `pyright src/spec_agents/knowledge/` — **0 errors, 0 warnings** with
  `--pythonpath C:\Users\ghendrick\AppData\Local\Programs\Python\Python312\python.exe`.
  Output includes one pre-existing config warning ("Config 'strict' entry
  must contain an array") that does not affect this task's code.
- [x] `ruff check src/spec_agents/knowledge/ tests/test_lenses.py` —
  **"All checks passed!"**. One SIM110 was emitted on first pass
  (collapsible for-loop in `_section_present`); fixed to `any(...)`
  before commit.
- [x] `ruff format --check src/spec_agents/knowledge/ tests/test_lenses.py` —
  **"3 files already formatted"**.
- [x] `git diff --name-only HEAD` matches `files.touched` in the task spec:
  ```
  docs/CURRENT_STATE.md
  src/spec_agents/knowledge/__init__.py
  src/spec_agents/knowledge/lenses.py
  tests/test_lenses.py
  ```
  Plus the new task-spec file at `.agent/tasks/spec-agents-lens-validator.md`
  (created by `agent-task new`; expected — not in must-not-touch).

## Acceptance criteria

- [x] **LensLoader exposes a public `validate()` method returning
  `list[ValidationIssue]`.**
  Evidence: `src/spec_agents/knowledge/lenses.py:174-203` — new method;
  signature `def validate(self) -> list[ValidationIssue]:`. Re-exported from
  `spec_agents.knowledge` per `__init__.py:6-12`.

- [x] **`ValidationIssue` distinguishes `doc_missing` from `header_missing`.**
  Evidence: `lenses.py:67-83` — frozen dataclass with `kind: str` field. Two
  literal values used in `validate()` (`lenses.py:184` and `lenses.py:198`).
  Test coverage: `test_validate_detects_missing_doc` asserts `kind ==
  "doc_missing"`; `test_validate_detects_missing_header` asserts the full
  `ValidationIssue(... kind="header_missing")`.

- [x] **`LensLoader.__init__` auto-invokes `validate()` and emits one
  `log.warning` per issue; never raises.**
  Evidence: `lenses.py:151-160` — `for issue in self.validate(): log.warning(
  "knowledge.lens_validation_issue", lens=..., doc=..., header=..., kind=...)`.
  Test coverage: `test_init_emits_warning_per_issue_without_raising` uses
  `structlog.testing.capture_logs()` and asserts 2 warning events for a
  3-section lens with 1 valid + 2 broken sections. Construction succeeds;
  the loader is then exercised via `load_lens("mixed")` to confirm normal
  operation on the valid section.

- [x] **4 new unit tests cover: clean lens, missing-header, missing-doc,
  init-warns-without-raising.**
  Evidence: `tests/test_lenses.py:94-161`. Test names:
  - `test_validate_clean_lens_returns_empty` — all sections resolve, validate() returns []
  - `test_validate_detects_missing_header` — doc exists, header typo → 1 header_missing issue
  - `test_validate_detects_missing_doc` — doc absent → 1 doc_missing issue
  - `test_init_emits_warning_per_issue_without_raising` — caplog assertion + post-init load_lens() still works

- [x] **`docs/CURRENT_STATE.md` adds `LensLoader.validate` /
  `ValidationIssue` to the public-surface list.**
  Evidence: `docs/CURRENT_STATE.md:50-57` — knowledge layer entry now lists
  `ValidationIssue` alongside existing types + describes the eager
  warning-mode validation.

- [x] **`pytest -q` clean (now 63 + 4 = 67 passing).**
  Evidence: see Automated checks above.

- [x] **`ruff check + ruff format --check` clean.**
  Evidence: see Automated checks above.

- [x] **No version bump.**
  Evidence: `pyproject.toml` is in `files.must-not-touch`; `git diff --stat`
  shows it unchanged. Kernel-freeze posture preserved.

## Out-of-scope confirmation

- [x] **No files in `files.must-not-touch` were modified.**
  Evidence: `git diff --name-only HEAD` returns only 4 files, all of which
  are in `files.touched`. `pyproject.toml`, `src/spec_agents/agents/`,
  `src/spec_agents/eval/`, `src/spec_agents/storage/`, `src/spec_agents/ingestion/`,
  `src/spec_agents/messages.py`, `src/spec_agents/testing/`, and all other
  test files are untouched. Cross-stack repos (spectacular, personal_os,
  photo_archive, planning, lightwork) are not touched by this worktree.

## Things I deliberately did not do

- **Add `tests/conftest.py` with `sys.path.insert(0, str(Path(__file__).parent.parent / "src"))`.**
  spec_agents currently has no `conftest.py`; tests run against the
  pip-installed `spec_agents` (in site-packages), not the worktree `src/`.
  I worked around this by running `PYTHONPATH=src pytest` for verification.
  This means my new tests will not run against the worktree code in any
  environment that doesn't set PYTHONPATH (including CI, depending on its
  install pattern). **The fix is a 5-line `conftest.py`** matching the
  pattern already in spectacular/personal_os/photo_archive (per the
  2026-05-21 retro: "tests/conftest.py worktree-sys.path fix × 4 repos" —
  spec_agents was apparently NOT one of those 4). Out of scope here
  because it's not in `files.touched`. **Recommended follow-up:**
  `chore: add tests/conftest.py for worktree imports` (3-line task).

- **Fix the `pyproject.toml` version drift** (declares `0.4.0`; tags +
  CURRENT_STATE claim `v0.6.0`). Pre-existing; not in scope.

- **Fix the pyright `Config "strict" entry must contain an array`** config
  warning. Pre-existing; not in scope; no impact on this task's correctness.

- **Hardening `_extract_section`'s existing lazy warning.** The lazy
  warning at `lenses.py:103-107` remains as-is — the eager validate() is
  additive. Consumer code that calls `load_lens()` on a Lens with broken
  sections will still get the existing lazy warning per-call. That's fine.

- **CLI / script wrapper around `validate()`.** Callers invoke
  `loader.validate()` programmatically; no CLI in this PR.

## Risks for human reviewer

1. **PYTHONPATH workaround is a verification gap.** If spec_agents CI
   uses `pip install -e .` and the wheel-installed package is on the
   path (not the source), then CI is testing the OLD `lenses.py` against
   the NEW `tests/test_lenses.py`. That would surface as an import error
   on `ValidationIssue` — CI will fail loudly, which is fine. The
   `chore: conftest` follow-up is the right durable fix. If CI is
   currently green for spec_agents, it's because tests already run
   against the installed package; my new test for `ValidationIssue`
   will force a re-install / re-export before CI passes.

2. **`structlog.testing.capture_logs()` is a relatively niche API.**
   The test should be robust (it's used in structlog's own test suite
   as a public utility), but if a future structlog major bump removes
   it, the test breaks. Mitigation: pinned per `pyproject.toml`. Low
   risk.

3. **`_section_present` reads the doc fully into memory.** For very
   large reference docs (hundreds of MB), that's wasteful. Real lens
   docs are KBs to low-MB at most — fine. Worth noting if someone ever
   adds a lens that points at a massive doc.

## Documentation drift (per the drift-audit lens)

- [x] **`docs/CURRENT_STATE.md` in this repo still matches reality.**
  Master commit bumped to `792f116`; recent landings list updated;
  test count 63 → 67; `python -m pytest -q` instruction count refreshed
  to 67; public-surface section now lists `ValidationIssue` and
  describes the eager-warning behavior.
- [x] **Cross-repo claims this change affects.** `planning/HANDOVER.md`
  doesn't claim anything specific about `LensLoader`'s validation
  behavior; no edit needed. `planning/decisions/D-citations-files-pdf.md`
  Move 1 reference now has a concrete shipping artifact; could be
  appended at the operator's discretion (follow-up, not blocking).
- [x] **Memory entries.** None reference LensLoader state.
- [x] **All path references resolve.** References in this verification
  doc + the task spec all point at real paths.

## Diff summary

- 4 files changed, +179 / -9 lines:
  - `src/spec_agents/knowledge/lenses.py` (+72 / -4): new
    `ValidationIssue` dataclass, new `_section_present` helper, new
    `LensLoader.validate()` method, init-time validation loop.
  - `src/spec_agents/knowledge/__init__.py` (+8 / -1): re-export
    `ValidationIssue`.
  - `tests/test_lenses.py` (+85 / -2): 4 new tests covering the
    validation surface + `structlog.testing.capture_logs` import.
  - `docs/CURRENT_STATE.md` (+14 / -2): master-commit bump, test count
    63 → 67, public-surface knowledge-layer entry expanded.

Plus 1 new file: `.agent/tasks/spec-agents-lens-validator.md` — task spec
(scaffold from `agent-task new`; filled in by this agent).

## Verdict

**Ready to merge.** All gates green, scope held, documentation refreshed,
known limitations honestly disclosed. Follow-up `chore: add
tests/conftest.py` recommended but not blocking — current verification
ran with `PYTHONPATH=src`.
