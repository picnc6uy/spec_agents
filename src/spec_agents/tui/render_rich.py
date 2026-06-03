"""Render a :class:`~spec_agents.tui.blocks.View` to the terminal with Rich.

Follows ``planning/terminal-output.md``: shared Console, semantic colors,
right-justified numbers, unicode bars. ``rich`` is imported lazily so importing
the kit doesn't require it until you actually render to a terminal.
"""

from __future__ import annotations

import contextlib
import sys

from .blocks import (
    Badges,
    BarTable,
    Note,
    Table,
    View,
    bar_color,
    format_value,
    tone,
)

# Bar column width, in cells — mirrors cost_reconcile's v0 (28-cell unicode bar).
_BAR_CELLS = 28


def _build_console():
    """Build a Console safe for legacy Windows consoles (cp1252 crashes on █/→).

    Reconfigure stdout to utf-8 first, then disable legacy_windows so rich emits
    the unicode glyphs instead of falling back. Mirrors cost_reconcile's v0.
    """
    from rich.console import Console

    with contextlib.suppress(AttributeError, ValueError):
        sys.stdout.reconfigure(encoding="utf-8")
    return Console(legacy_windows=False)


def render_rich(view: View, console=None) -> None:
    """Print ``view`` to ``console`` (built if None). Offline, no network."""
    from rich import box
    from rich.panel import Panel
    from rich.table import Table as RichTable
    from rich.text import Text

    if console is None:
        console = _build_console()

    # View header: title (cyan, per house style) then dim subtitle.
    console.print()
    console.print(Text(view.title, style="bold cyan"))
    if view.subtitle:
        console.print(Text(view.subtitle, style="dim"))

    for block in view.blocks:
        if isinstance(block, Badges):
            _render_badges(console, block, Text)
        elif isinstance(block, BarTable):
            console.print(_bar_table(block, RichTable, Text, box))
        elif isinstance(block, Note):
            console.print(_note_panel(block, Panel, Text))
        elif isinstance(block, Table):
            console.print(_plain_table(block, RichTable))
    console.print()


def _render_badges(console, badges: Badges, Text) -> None:
    line = Text()
    for badge in badges.items:
        t = tone(badge.tone)
        line.append(f" {badge.label} ", style="dim")
        line.append(f"{badge.value}  ", style=t.rich)
    console.print(line)


def _bar_table(block: BarTable, RichTable, Text, box) -> object:
    t = RichTable(
        title=block.title,
        title_justify="left",
        title_style="bold cyan",
        box=box.SIMPLE,
        expand=False,
        pad_edge=False,
    )
    t.add_column("item", no_wrap=True, style="dim")
    t.add_column("bar", no_wrap=True)
    t.add_column("value", justify="right", no_wrap=True)

    rows = block.sorted_rows()
    default_style = bar_color(block.color).rich
    mx = max((r.value for r in rows), default=1.0) or 1.0
    if not rows:
        t.add_row("(none)", "", "")
    for row in rows:
        n = int(round(row.value / mx * _BAR_CELLS)) if row.value > 0 else 0
        style = tone(row.tone).rich if row.tone else default_style
        t.add_row(
            row.label,
            Text("█" * n, style=style),
            format_value(row.value, block.unit),
        )
    return t


def _note_panel(block: Note, Panel, Text) -> object:
    t = tone(block.tone)
    return Panel(
        Text(block.text, style=t.rich),
        title=block.title,
        title_align="left",
        border_style=t.rich,
        expand=False,
    )


def _plain_table(block: Table, RichTable) -> object:
    t = RichTable(
        title=block.title,
        title_justify="left",
        title_style="bold cyan",
        box=None,
        expand=False,
        pad_edge=False,
    )
    for i, col in enumerate(block.columns):
        # First column is the label (dim); the rest right-justify like numbers.
        if i == 0:
            t.add_column(col, style="dim", no_wrap=True)
        else:
            t.add_column(col, justify="right")
    for row in block.rows:
        t.add_row(*[str(c) for c in row])
    return t
