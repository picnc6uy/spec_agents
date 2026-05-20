# spec_agents — Canonical Conventions

What `spec_agents` expects of itself and of its consumers. These are the
defaults across the canonical stack (`spec_agents`, `spectacular`,
`personal_os`, `photo_archive`). Deviations should be justified per-repo,
not adopted casually.

This file is the spec_agents-side companion to whatever ends up canonical
across the stack via XR-006. Until that lands, treat this file as the
authority for consumers integrating against `spec_agents`.

---

## Language and runtime

- **Python ≥ 3.12.** Use modern syntax (`str | None`, `match`, parametric
  type aliases). No `typing.Optional`, no `typing.List`.
- **Type hints are not optional.** Every public function annotates its
  signature; pyright strict catches escapees in CI.

## Lint and format

- **Ruff** with this profile (also in `pyproject.toml`):
  - `line-length = 100`
  - `target-version = "py312"`
  - `select = ["E", "F", "I", "UP", "B", "SIM"]`
  - `ignore = ["E501"]` (line length warnings ignored — ruff-format is the truth)
- **Ruff-format** is the formatter. Never hand-format.
- **Pyright strict** for `src/`. The pyproject config is checked in; consumers
  inherit it via editable install.

## Pre-commit

Minimum hook set across the stack:

- `ruff` (with `--fix`) and `ruff-format`
- `detect-secrets` against a per-repo `.secrets.baseline`
- `pre-commit-hooks`: trailing-whitespace, end-of-file-fixer, check-yaml,
  check-toml, check-merge-conflict, check-added-large-files (500KB cap),
  detect-private-key

Pyright is intentionally **not** in the hook by default — it lives in CI
(XR-008) to keep commits fast. Consumers may add it if they like.

## Public surface (what consumers depend on)

Documented in [CLAUDE.md](../CLAUDE.md). Do not break the listed symbols
without a version bump and coordination with consumers. Pinned in
[CURRENT_STATE.md](CURRENT_STATE.md).

## Message and data contracts

- **Pydantic v2 for all cross-boundary types** (`spec_agents.messages`).
  Validators encode invariants (e.g. `invalidation_conditions` non-empty).
- **Dataclasses for internal DTOs** (`RawMetricIn`) — no validation overhead
  where the caller is trusted code.
- **Generic agent message protocol does not change without a version bump.**
  Stored agent outputs reference the schema by structure; a breaking change
  invalidates the corpus.

## Storage

- **SQLAlchemy 2.0+** with the 2.0 select API (`session.execute(select(...))`),
  not the legacy `query()` API.
- **No dialect-specific imports** outside dialect-check guards. Writes stay
  Postgres-portable.
- **Idempotent ingestion is non-negotiable.** Use `UniqueConstraint` +
  per-row savepoints (`session.begin_nested()`); never `INSERT … ON DUPLICATE`
  except behind a dialect guard.

## Logging

- **structlog** with the JSON-capable processor chain (`spec_agents.logging.setup`).
- No `print()` in library code. No bespoke loggers.
- Never log secret values. Never log full request bodies that may contain PII.

## Adapter pattern

- Every data source inherits from `spec_agents.ingestion.adapters.base.Adapter`.
- Subclasses set the five class attributes: `source`, `source_version`,
  `expected_cadence`, `staleness_threshold`, `priority`.
- `fetch()` returns `list[RawMetricIn]`; raises on unrecoverable errors;
  callers handle retry.
- One adapter per (source, asset) pair. No multi-source adapters.

## Lens pattern (knowledge layer)

- Lenses are named, focused extracts from reference docs. ~3000–6000 chars
  (~750–1500 tokens) each.
- Header-anchored, not character-range — stable across doc edits.
- Composed by agents based on the data they're reasoning about; prefer
  specificity over breadth.

## Testing

- **pytest** with `testpaths = ["tests"]` in `pyproject.toml`.
- Smoke tests guard the public surface (see `tests/test_imports.py` for the
  template).
- No live API calls in unit tests. Integration tests are marked
  `@pytest.mark.integration` and excluded from the default run.
- Tests must run without network access. Use `tmp_path` for filesystem,
  in-memory SQLite for storage, fixtures for HTTP responses.

## Secrets

- **Never** commit secrets. `detect-secrets` enforces this at commit time.
- All secrets live in `.env` (gitignored). Each repo ships `.env.example`.
- Rotation cadence: 90 days (calendar reminder per XR-002).

## When in doubt

Match what `spec_agents` itself does. If `spec_agents` is wrong, fix it
here first, then propagate. This file is the truth; consumers should not
fork conventions silently.
