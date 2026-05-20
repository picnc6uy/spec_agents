"""Curated reference-doc lenses (domain-agnostic).

A "lens" is a named, focused extract from one or more reference docs. Each
lens specifies a list of (doc_filename, section_header) pairs. The loader
extracts each section from the start of its header line to the next header
at the same or higher level (e.g., asking for `## 1.2` extracts everything
up to the next `## ...` or `# ...`, including any `### 1.2.x` subsections).

Header-anchored extraction is preferable to char-range because:
  - Stable across doc edits (as long as headers don't change)
  - Self-documenting (the lens declares which sections it cares about)
  - Cache-friendly (same lens content → same cache key under prompt caching)

Lens design principles:
  - Each lens is ~3000-6000 chars (~750-1500 tokens)
  - Lenses are composed by agents based on the data they're reasoning about
  - When unsure, prefer specificity over breadth — narrow lenses load faster
    and reduce noise in the agent's reasoning context

USAGE:
    from spec_agents.knowledge import LensLoader, Lens, LensSection

    LENSES = {
        "my_lens": Lens(
            name="my_lens",
            description="...",
            sections=(
                LensSection("doc.md", "## Some Section"),
                ...
            ),
        ),
    }

    loader = LensLoader(docs_root=Path("./docs"), lenses=LENSES)
    text = loader.load_lens("my_lens")
    combined = loader.load_lenses(["my_lens", "other_lens"])
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import structlog

log = structlog.get_logger()


@dataclass(frozen=True)
class LensSection:
    """A single section to extract from a reference doc."""

    doc: str
    header: str  # exact match including leading #s, e.g. "## 1.2 Funding Rate and Basis Strategies"


@dataclass(frozen=True)
class Lens:
    """A named, focused extract from one or more reference docs."""

    name: str
    description: str
    sections: tuple[LensSection, ...]


# ── Section-extraction helpers ────────────────────────────────────────────────


def _header_level(line: str) -> int:
    """Return the markdown header level (number of leading #s), or 0 if not a header."""
    stripped = line.lstrip()
    if not stripped.startswith("#"):
        return 0
    n = 0
    for ch in stripped:
        if ch == "#":
            n += 1
        else:
            break
    # Must be followed by space or end-of-line to count as a header
    if n < len(stripped) and stripped[n] not in (" ", "\t"):
        return 0
    return n


def _extract_section(doc_path: Path, header: str) -> str:
    """Extract a section starting at the matching header until the next same-or-higher header."""
    if not doc_path.exists():
        log.warning("knowledge.doc_missing", path=str(doc_path))
        return ""

    text = doc_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    target = header.strip()

    start_idx: int | None = None
    for i, line in enumerate(lines):
        if line.strip() == target:
            start_idx = i
            break

    if start_idx is None:
        log.warning(
            "knowledge.section_not_found",
            doc=doc_path.name,
            header=header,
        )
        return ""

    target_level = _header_level(target)
    end_idx = len(lines)
    for j in range(start_idx + 1, len(lines)):
        line_level = _header_level(lines[j])
        if 0 < line_level <= target_level:
            end_idx = j
            break

    return "\n".join(lines[start_idx:end_idx]).rstrip()


# ── LensLoader ────────────────────────────────────────────────────────────────


class LensLoader:
    """Loads lenses from a docs root + lens definition dict.

    Caching: per-(loader-instance, lens-name) via lru_cache on a bound method.
    Two different LensLoader instances (different docs_root) cache independently.
    """

    def __init__(self, docs_root: Path, lenses: dict[str, Lens]) -> None:
        self.docs_root = Path(docs_root)
        self.lenses = dict(lenses)
        # Per-instance cache so two loaders don't share cached text
        self._cache: dict[str, str] = {}

    def list_lenses(self) -> list[str]:
        """Return all available lens names sorted."""
        return sorted(self.lenses)

    def load_lens(self, name: str) -> str:
        """Load a single lens as a markdown text block ready for prompt injection."""
        if name in self._cache:
            return self._cache[name]
        if name not in self.lenses:
            raise KeyError(f"Unknown lens: {name!r}. Available: {sorted(self.lenses)}")
        lens = self.lenses[name]
        parts: list[str] = [
            f"# Lens: {lens.name}",
            f"_{lens.description}_",
            "",
        ]
        for sec in lens.sections:
            section_text = _extract_section(self.docs_root / sec.doc, sec.header)
            if not section_text:
                continue
            parts.append(f"## Source: {sec.doc}")
            parts.append("")
            parts.append(section_text)
            parts.append("")
        text = "\n".join(parts).rstrip()
        self._cache[name] = text
        return text

    def load_lenses(self, names: list[str]) -> str:
        """Load multiple lenses joined with horizontal rules."""
        if not names:
            return ""
        blocks = [self.load_lens(n) for n in names if n in self.lenses]
        return "\n\n---\n\n".join(b for b in blocks if b)
