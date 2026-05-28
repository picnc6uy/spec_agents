"""Smoke test: the LensLoader extracts named sections from markdown docs.

Confirms header-anchored extraction, cache behavior, unknown-lens
errors, and (since spec-agents-lens-validator 2026-05-28) startup
validation of `(lens, section)` triples. Uses `tmp_path` to avoid
coupling to any specific docs/ layout.
"""

from pathlib import Path

import pytest
from structlog.testing import capture_logs

from spec_agents.knowledge.lenses import (
    Lens,
    LensLoader,
    LensSection,
    ValidationIssue,
)

_DOC = """\
# Top-level

Intro text.

## Section A

Content of A line 1.
Content of A line 2.

## Section B

Content of B.

### Section B.1

Subsection content.

## Section C

Should not be in A or B.
"""


def _make_loader(tmp_path: Path) -> LensLoader:
    (tmp_path / "doc.md").write_text(_DOC, encoding="utf-8")
    lenses = {
        "a_only": Lens(
            name="a_only",
            description="just section A",
            sections=(LensSection("doc.md", "## Section A"),),
        ),
        "b_with_sub": Lens(
            name="b_with_sub",
            description="section B and its subsection",
            sections=(LensSection("doc.md", "## Section B"),),
        ),
    }
    return LensLoader(docs_root=tmp_path, lenses=lenses)


def test_load_lens_extracts_section(tmp_path: Path) -> None:
    loader = _make_loader(tmp_path)
    text = loader.load_lens("a_only")
    assert "Content of A line 1." in text
    assert "Content of A line 2." in text
    assert "Content of B." not in text
    assert "Should not be in A or B." not in text


def test_load_lens_includes_subsections(tmp_path: Path) -> None:
    loader = _make_loader(tmp_path)
    text = loader.load_lens("b_with_sub")
    assert "Content of B." in text
    assert "### Section B.1" in text
    assert "Subsection content." in text
    assert "Should not be in A or B." not in text


def test_unknown_lens_raises(tmp_path: Path) -> None:
    loader = _make_loader(tmp_path)
    with pytest.raises(KeyError, match="Unknown lens"):
        loader.load_lens("not_a_lens")


def test_list_lenses_returns_sorted_names(tmp_path: Path) -> None:
    loader = _make_loader(tmp_path)
    assert loader.list_lenses() == ["a_only", "b_with_sub"]


# ── Startup-validation tests (spec-agents-lens-validator 2026-05-28) ────────


def test_validate_clean_lens_returns_empty(tmp_path: Path) -> None:
    """All sections resolve → validate() returns []."""
    loader = _make_loader(tmp_path)
    assert loader.validate() == []


def test_validate_detects_missing_header(tmp_path: Path) -> None:
    """Doc exists but header isn't found → one header_missing issue."""
    (tmp_path / "doc.md").write_text(_DOC, encoding="utf-8")
    lenses = {
        "bad_header": Lens(
            name="bad_header",
            description="header typo",
            sections=(LensSection("doc.md", "## Section X (does not exist)"),),
        ),
    }
    loader = LensLoader(docs_root=tmp_path, lenses=lenses)
    issues = loader.validate()
    assert len(issues) == 1
    assert issues[0] == ValidationIssue(
        lens_name="bad_header",
        doc="doc.md",
        header="## Section X (does not exist)",
        kind="header_missing",
    )


def test_validate_detects_missing_doc(tmp_path: Path) -> None:
    """Doc file not present → one doc_missing issue; no I/O attempted on header."""
    lenses = {
        "ghost_doc": Lens(
            name="ghost_doc",
            description="refers to a file that doesn't exist",
            sections=(LensSection("nonexistent.md", "## Anything"),),
        ),
    }
    loader = LensLoader(docs_root=tmp_path, lenses=lenses)
    issues = loader.validate()
    assert len(issues) == 1
    assert issues[0].kind == "doc_missing"
    assert issues[0].doc == "nonexistent.md"


def test_init_emits_warning_per_issue_without_raising(tmp_path: Path) -> None:
    """LensLoader.__init__ logs one warning per validation issue; construction succeeds."""
    (tmp_path / "doc.md").write_text(_DOC, encoding="utf-8")
    lenses = {
        "mixed": Lens(
            name="mixed",
            description="one valid + one broken section",
            sections=(
                LensSection("doc.md", "## Section A"),  # valid
                LensSection("doc.md", "## Section ZZZ"),  # header_missing
                LensSection("ghost.md", "## Anything"),  # doc_missing
            ),
        ),
    }
    with capture_logs() as cap_logs:
        loader = LensLoader(docs_root=tmp_path, lenses=lenses)  # must not raise
    warning_events = [e for e in cap_logs if e.get("event") == "knowledge.lens_validation_issue"]
    assert (
        len(warning_events) == 2
    )  # one header_missing + one doc_missing; not for the valid section
    kinds = sorted(e["kind"] for e in warning_events)
    assert kinds == ["doc_missing", "header_missing"]
    # And the loader is fully usable for the valid section.
    text = loader.load_lens("mixed")
    assert "Content of A line 1." in text
