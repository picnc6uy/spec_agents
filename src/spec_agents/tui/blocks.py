"""Declarative, target-agnostic TUI building blocks.

These dataclasses describe *what* to render, not *how*. A renderer
(``render_rich`` for the terminal, ``render_html`` for an offline file)
walks a :class:`View` and turns each block into its target representation.

The vocabulary is intentionally small and operationalizes the house style in
``planning/terminal-output.md``: semantic tones (good/warn/bad/neutral), a
shared ``$``/count value formatter, and right-justified numbers. Nothing here
imports rich or touches I/O — the blocks are pure data, so they are trivially
testable and can target multiple renderers.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# --- Tone vocabulary -----------------------------------------------------------
# Each tone maps to (rich style, html color, html class). The renderers read
# from this single table so the terminal and HTML stay in lock-step.
@dataclass(frozen=True)
class Tone:
    """A semantic tone resolved to both a rich style and an html color/class."""

    rich: str
    html_color: str
    html_class: str


_TONE: dict[str, Tone] = {
    "neutral": Tone(rich="cyan", html_color="var(--cache)", html_class="neutral"),
    "good": Tone(rich="green", html_color="var(--output)", html_class="good"),
    "warn": Tone(rich="yellow", html_color="var(--cachew)", html_class="warn"),
    "bad": Tone(rich="red", html_color="var(--warn)", html_class="bad"),
}

# Color names usable as a BarTable.color / the default bar fill. "accent" is the
# kit's default and resolves to the neutral tone's color.
_ACCENT = "accent"


def tone(name: str | None) -> Tone:
    """Resolve a tone name to its :class:`Tone`, defaulting to neutral."""
    if not name:
        return _TONE["neutral"]
    return _TONE.get(name, _TONE["neutral"])


def bar_color(color: str) -> Tone:
    """Resolve a BarTable ``color`` (a tone name or ``"accent"``) to a Tone.

    ``"accent"`` aliases the neutral tone so the default bar still has a color.
    """
    if color == _ACCENT:
        return _TONE["neutral"]
    return tone(color)


# --- Value formatting ----------------------------------------------------------
def format_value(value: float, unit: str) -> str:
    """Format a numeric value for display.

    ``"$"`` -> ``$1,234.50`` (two decimals, thousands separators).
    ``""``  -> ``1,235`` (integer count, thousands separators).
    Any other unit is appended verbatim after a space-free ``,.0f``.
    """
    if unit == "$":
        return f"${value:,.2f}"
    if unit == "":
        return f"{value:,.0f}"
    return f"{value:,.0f}{unit}"


# --- Blocks --------------------------------------------------------------------
@dataclass
class Badge:
    """A single key/value chip. ``tone`` colors the value."""

    label: str
    value: str
    tone: str = "neutral"


@dataclass
class Badges:
    """A horizontal strip of :class:`Badge` chips."""

    items: list[Badge]


@dataclass
class BarRow:
    """One row of a :class:`BarTable`. ``tone`` overrides the table color."""

    label: str
    value: float
    tone: str | None = None


@dataclass
class BarTable:
    """A titled table of bar rows scaled to the section max.

    ``sort``: ``"value"`` (descending by value, the default), ``"label"``
    (ascending by label), or ``"none"`` (keep insertion order).
    ``color``: a tone name or ``"accent"`` for the default bar fill.
    """

    title: str
    rows: list[BarRow]
    unit: str = "$"
    color: str = "accent"
    sort: str = "value"

    def sorted_rows(self) -> list[BarRow]:
        """Return the rows ordered per ``sort`` (non-mutating)."""
        if self.sort == "label":
            return sorted(self.rows, key=lambda r: r.label)
        if self.sort == "none":
            return list(self.rows)
        # default: "value", descending
        return sorted(self.rows, key=lambda r: -r.value)


@dataclass
class Note:
    """A toned, optionally-titled prose block (renders as a rich Panel)."""

    text: str
    tone: str = "neutral"
    title: str | None = None


@dataclass
class Table:
    """A plain titled table of string cells (no bars)."""

    title: str
    columns: list[str]
    rows: list[list[str]]


@dataclass
class View:
    """The top-level container: a title/subtitle and an ordered block list."""

    title: str
    subtitle: str = ""
    blocks: list = field(default_factory=list)
