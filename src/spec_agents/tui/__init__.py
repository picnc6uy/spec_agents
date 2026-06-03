"""spec_agents.tui — a small, reusable terminal-UI kit.

Declarative blocks (:mod:`spec_agents.tui.blocks`) describe a dashboard once;
two renderers turn that description into either a Rich terminal view
(:func:`render_rich`) or a self-contained offline HTML page
(:func:`render_html`). The vocabulary operationalizes the house style in
``planning/terminal-output.md`` (Rich default; semantic tones; right-justified
numbers; shared Console).

Nothing here makes a network call. ``rich`` is imported lazily inside
``render_rich`` so importing the kit (or rendering HTML) needs no extra deps.

Example::

    from spec_agents.tui import View, Badge, Badges, BarRow, BarTable, render_rich
    view = View("Demo", "subtitle", [
        Badges([Badge("billed", "$45.00", tone="bad")]),
        BarTable("Spend", [BarRow("input", 40.0), BarRow("output", 5.0)]),
    ])
    render_rich(view)
"""

from __future__ import annotations

from .blocks import (
    Badge,
    Badges,
    BarRow,
    BarTable,
    Note,
    Table,
    Tone,
    View,
    bar_color,
    format_value,
    tone,
)
from .render_html import render_html
from .render_rich import render_rich

__all__ = [
    "Badge",
    "Badges",
    "BarRow",
    "BarTable",
    "Note",
    "Table",
    "Tone",
    "View",
    "bar_color",
    "format_value",
    "tone",
    "render_html",
    "render_rich",
]
