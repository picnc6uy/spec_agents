"""Interactive (Textual) renderers — the analog of :mod:`render_rich`.

Per ``planning/terminal-output.md``, Textual is justified ONLY when the output
must be *interactive* (navigate / scroll / filter). For a static print, use
:func:`spec_agents.tui.render_rich`.

``textual`` is an OPTIONAL dependency (declared as the ``textual`` extra in
spec_agents' pyproject, like keyring elsewhere). It is imported lazily so that
importing the kit, or rendering Rich/HTML, needs no extra deps. If textual is
absent both public functions raise a clear :class:`ImportError`.

This module reuses :mod:`render_rich`'s per-block Rich renderables so the
interactive view matches the printed one exactly. Nothing here makes a network
call.
"""

from __future__ import annotations

from collections.abc import Callable

from .blocks import (
    Badges,
    BarTable,
    Note,
    Table,
    View,
)

_IMPORT_HINT = (
    "spec_agents.tui interactive rendering needs Textual, which is an optional "
    "dependency. Install it with:  pip install textual   "
    "(or  pip install 'spec-agents[textual]')."
)


def _require_textual():
    """Import textual lazily, re-raising with an actionable hint if absent."""
    try:
        import textual  # noqa: F401
    except ImportError as exc:  # pragma: no cover - exercised via the public API
        raise ImportError(_IMPORT_HINT) from exc


def _block_renderables(view: View) -> list[object]:
    """Turn a View's blocks into a flat list of Rich renderables.

    Reuses render_rich's private builders so the interactive view is pixel-for-
    pixel the same as the printed one. rich is imported here (textual depends on
    rich, so it is always present once textual is).
    """
    from rich import box
    from rich.console import Group
    from rich.panel import Panel
    from rich.table import Table as RichTable
    from rich.text import Text

    from .render_rich import _bar_table, _note_panel, _plain_table

    out: list[object] = []
    # View header (title + optional subtitle) as a small Group, matching render_rich.
    header_parts: list[object] = [Text(view.title, style="bold cyan")]
    if view.subtitle:
        header_parts.append(Text(view.subtitle, style="dim"))
    out.append(Group(*header_parts))

    for block in view.blocks:
        if isinstance(block, Badges):
            line = Text()
            for badge in block.items:
                from .blocks import tone as _tone

                t = _tone(badge.tone)
                line.append(f" {badge.label} ", style="dim")
                line.append(f"{badge.value}  ", style=t.rich)
            out.append(line)
        elif isinstance(block, BarTable):
            out.append(_bar_table(block, RichTable, Text, box))
        elif isinstance(block, Note):
            out.append(_note_panel(block, Panel, Text))
        elif isinstance(block, Table):
            out.append(_plain_table(block, RichTable))
    return out


def _ViewApp_factory(view: View):
    """Build (but do not run) the scrollable single-View Textual app.

    Split out from :func:`render_textual` so the headless test harness can mount
    the same app via ``app.run_test()`` instead of taking over a real terminal.
    """
    _require_textual()

    from rich.console import Group
    from textual.app import App, ComposeResult
    from textual.containers import VerticalScroll
    from textual.widgets import Static

    renderables = _block_renderables(view)

    class _ViewApp(App):  # type: ignore[misc]
        BINDINGS = [("q", "quit", "Quit")]
        TITLE = view.title or "spec_agents.tui"

        def compose(self) -> ComposeResult:
            yield VerticalScroll(Static(Group(*renderables), id="view-body"))

    app = _ViewApp()
    # Exposed for headless tests — the View this app is showing.
    app.shown_view = view  # type: ignore[attr-defined]
    return app


def render_textual(view: View) -> None:
    """Render ``view``'s blocks scrollably in a Textual app. ``q`` quits.

    The generic interactive analog of :func:`render_rich`: same blocks, same
    Rich renderables, but inside a scrollable container so the operator can
    navigate a tall view. Blocks until the operator quits.
    """
    _ViewApp_factory(view).run()


def _BrowserApp_factory(
    *,
    rows: list[dict],
    columns: list[str],
    detail: Callable[[dict], View],
    title: str = "",
):
    """Build (but do not run) the master-detail browser app.

    Split out from :func:`record_browser` so the headless test harness can mount
    the same app via ``app.run_test()`` instead of taking over a real terminal.
    """
    _require_textual()

    from rich.console import Group
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal
    from textual.widgets import DataTable, Input, Static

    def _cell(row: dict, col: str) -> str:
        v = row.get(col, "")
        return "" if v is None else str(v)

    class _BrowserApp(App):  # type: ignore[misc]
        BINDINGS = [("q", "quit", "Quit"), ("slash", "focus_filter", "Filter")]
        TITLE = title or "record browser"

        def __init__(self) -> None:
            super().__init__()
            self._all_rows = rows
            self._visible: list[dict] = list(rows)

        def compose(self) -> ComposeResult:
            with Horizontal():
                yield DataTable(id="master", cursor_type="row")
                yield Static("", id="detail")
            yield Input(placeholder="filter…", id="filter")

        def on_mount(self) -> None:
            table = self.query_one("#master", DataTable)
            table.add_columns(*columns)
            self._populate(self._visible)
            self.query_one("#filter", Input).display = False
            table.focus()
            self._render_detail(0)

        def _populate(self, visible: list[dict]) -> None:
            table = self.query_one("#master", DataTable)
            table.clear()
            for row in visible:
                table.add_row(*[_cell(row, c) for c in columns])
            self._visible = visible

        def _render_detail(self, index: int) -> None:
            pane = self.query_one("#detail", Static)
            if not self._visible:
                self.detail_view = None  # type: ignore[attr-defined]
                pane.update("(no matching rows)")
                return
            index = max(0, min(index, len(self._visible) - 1))
            view = detail(self._visible[index])
            # Expose the current detail View for headless tests (Textual's Static
            # does not surface its content as a public attribute in 8.x).
            self.detail_view = view  # type: ignore[attr-defined]
            pane.update(Group(*_block_renderables(view)))

        # Cursor movement in the DataTable -> re-render the detail pane.
        def on_data_table_row_highlighted(self, event) -> None:  # type: ignore[no-untyped-def]
            self._render_detail(event.cursor_row)

        def action_focus_filter(self) -> None:
            inp = self.query_one("#filter", Input)
            inp.display = True
            inp.focus()

        def _apply_filter(self, term: str) -> None:
            term = term.strip().lower()
            if not term:
                visible = list(self._all_rows)
            else:
                visible = [
                    r for r in self._all_rows if any(term in _cell(r, c).lower() for c in columns)
                ]
            self._populate(visible)
            self._render_detail(0)

        def on_input_changed(self, event) -> None:  # type: ignore[no-untyped-def]
            self._apply_filter(event.value)

        def on_input_submitted(self, event) -> None:  # type: ignore[no-untyped-def]
            inp = self.query_one("#filter", Input)
            inp.display = False
            self.query_one("#master", DataTable).focus()

    return _BrowserApp()


def record_browser(
    *,
    rows: list[dict],
    columns: list[str],
    detail: Callable[[dict], View],
    title: str = "",
) -> None:
    """Master-detail Textual browser over ``rows``.

    Left: a :class:`~textual.widgets.DataTable` showing ``columns`` of each row.
    Right: a detail pane that re-renders whenever the cursor moves, by calling
    ``detail(row) -> View`` and rendering that View's blocks.

    Keys: ↑/↓ navigate, ``/`` filter the table (substring across the shown
    columns; Enter/Escape closes the filter), ``q`` quit. Blocks until quit.
    """
    _BrowserApp_factory(rows=rows, columns=columns, detail=detail, title=title).run()
