"""Smoke test: the LensLoader extracts named sections from markdown docs.

Confirms header-anchored extraction, cache behavior, and unknown-lens
errors. Uses tmp_path to avoid coupling to any specific docs/ layout.
"""

from pathlib import Path

import pytest

from spec_agents.knowledge.lenses import Lens, LensLoader, LensSection

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
