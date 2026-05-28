---
id: spec-agents-lens-validator
title: Add LensLoader startup validation (catches heading-coupling brittleness at construction)
type: new-feature
lens: new-feature
created: 2026-05-28
status: drafted
acceptance:
  - "LensLoader exposes a public validate() method returning list[ValidationIssue]"
  - "ValidationIssue distinguishes doc_missing from header_missing"
  - "LensLoader.__init__ auto-invokes validate() and emits log.warning per issue; never raises"
  - "4 new unit tests cover: clean lens, missing-header, missing-doc, init-warns-without-raising"
  - "docs/CURRENT_STATE.md adds LensLoader.validate / ValidationIssue to the public-surface list"
  - "pytest -q clean (now 63 + 4 = 67 passing)"
  - "ruff check + ruff-format check clean"
  - "no version bump (kernel-freeze; pre-existing version drift in pyproject.toml is out of scope)"
files:
  touched:
    - src/spec_agents/knowledge/lenses.py
    - src/spec_agents/knowledge/__init__.py
    - tests/test_lenses.py
    - docs/CURRENT_STATE.md
  must-not-touch:
    - pyproject.toml
    - src/spec_agents/agents/
    - src/spec_agents/eval/
    - src/spec_agents/storage/
    - src/spec_agents/ingestion/
    - src/spec_agents/messages.py
    - src/spec_agents/testing/
    - all other test files
    - .agent/
    - planning/
    - any other repo (spectacular, personal_os, photo_archive)
---

# spec-agents-lens-validator: Add LensLoader startup validation

## Why

Follow-up Move 1 queued by `planning/decisions/D-citations-files-pdf.md` (DECLINE
signed 2026-05-28 — full Files+Citations migration declined; this small refactor
addresses the underlying heading-coupling brittleness instead).

Current behavior: when an operator edits a reference doc and changes a heading
from `## Funding Rate Strategies` to `## Funding Rate Strategies (2026 revision)`,
the `LensSection` reference silently fails. `_extract_section()` already emits
`log.warning("knowledge.section_not_found", ...)` (lenses.py:103-107), but this
fires LAZILY on first `load_lens()` call — and only into a structured log line
that nothing scrapes. Result: the synthesizer prompt runs with incomplete
context and the operator may never notice.

This task makes the existing warning EAGER (fires at `LensLoader.__init__` for
every broken section across every lens) and adds a programmatic surface
(`validate()` returning `list[ValidationIssue]`) so callers can react beyond
log-scraping.

## What

Public surface additions in `spec_agents.knowledge.lenses`:

1. New frozen dataclass `ValidationIssue`:
   ```python
   @dataclass(frozen=True)
   class ValidationIssue:
       lens_name: str
       doc: str
       header: str
       kind: str  # "doc_missing" | "header_missing"
   ```

2. New `LensLoader.validate() -> list[ValidationIssue]` method:
   - Iterates `(lens_name, section)` triples in deterministic order.
   - For each section: checks doc file exists; if it does, checks the
     header line exists in the doc.
   - Returns `[]` when clean.
   - Does not raise; never mutates loader state.

3. `LensLoader.__init__` calls `self.validate()` once at construction and
   emits one `log.warning("knowledge.lens_validation_issue", ...)` per
   issue. Construction never fails on validation issues (warning mode per
   memo — the operator may load a partially-valid lens set deliberately
   during a doc edit).

4. New module-private helper `_section_present(doc_path, header) -> bool`
   for the lightweight existence check. Does NOT log (`_extract_section`
   already handles that path).

5. Re-export `ValidationIssue` from `spec_agents.knowledge.__init__` so
   consumers can `from spec_agents.knowledge import ValidationIssue`.

## Out of scope

- **Version bump in pyproject.toml.** Pre-existing drift: pyproject.toml
  says 0.4.0; CURRENT_STATE.md claims v0.6.0. That's a separate hygiene
  task — flagged in the verification doc but NOT fixed here. Kernel-freeze
  posture also argues against bumping in this PR.
- **Hardening `_extract_section`'s existing warning** — that lazy warning
  remains as-is. The eager `validate()` is additive, not a replacement.
- **CLI for running validation outside __init__** — callers can invoke
  `loader.validate()` programmatically; no CLI wrapper this cycle.
- **Lens auto-repair / heading suggestion.** If a header is missing, we
  warn; we do not propose alternatives. That's a future LENS-* task.
- **Anything in spectacular / personal_os.** Consumers benefit
  automatically when they construct their LensLoader; their code does
  not change.
- **D-7 lens-sync-precommit-01.** Still queued separately; orthogonal.

## Notes

- **Warning mode rationale:** the memo explicitly recommends warning
  mode. Crashing on validation would break daily-brief runs whenever
  the operator is mid-edit on a reference doc. Warnings + a programmatic
  surface let consumers decide their own failure stance.
- **Stable iteration order:** `dict.items()` preserves insertion order
  (Python 3.7+), so issue ordering matches lens declaration order. No
  sorted() needed.
- **Caching:** `validate()` reads each unique doc at most once per call,
  but does NOT populate `self._cache` (which holds full lens text, not
  per-doc raw text). No cache contract changes.
- **Logger:** uses the existing module-level `log = structlog.get_logger()`.

## References

- `planning/decisions/D-citations-files-pdf.md` — the DECLINE memo, Move 1
- `src/spec_agents/knowledge/lenses.py:86-118` — current `_extract_section`
  with lazy warning
- `src/spec_agents/knowledge/lenses.py:131-135` — current `LensLoader.__init__`
  signature
