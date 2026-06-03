"""Tests for spec_agents.tui interactive (Textual) renderers.

Uses Textual's headless harness (``async with app.run_test() as pilot:``) so no
real terminal is touched. The async bodies are driven via ``asyncio.run`` inside
plain sync tests, so this module needs no pytest-asyncio plugin.

The whole module skips cleanly when ``textual`` is not importable, so the
existing 18 tui tests never break on a textual-less env.

Fully offline: no network. ``textual`` (and its rich dep) are the only extra
requirements.
"""

from __future__ import annotations

import asyncio
import io

import pytest

# Skip the entire module if textual is absent — keeps the base suite green
# without the optional extra installed.
pytest.importorskip("textual")

from spec_agents.tui import (  # noqa: E402
    Badge,
    Badges,
    Note,
    View,
    record_browser,
    render_textual,
)
from spec_agents.tui.render_textual import (  # noqa: E402
    _block_renderables,
    _BrowserApp_factory,
    _ViewApp_factory,
)


# ---------------------------------------------------------------------------
# render_textual: mounts and shows a block's text
# ---------------------------------------------------------------------------
def test_render_textual_mounts_and_shows_block_text():
    view = View(
        "My Dashboard",
        "sub",
        [
            Badges([Badge("billed", "$45.00", tone="bad")]),
            Note("all clear", tone="good", title="Status"),
        ],
    )

    async def body():
        from textual.widgets import Static

        app = _ViewApp_factory(view)
        async with app.run_test() as pilot:
            await pilot.pause()
            # The Static mounts (proves the app composed without error)...
            assert app.query_one("#view-body", Static) is not None
            # ...and the block text it was built from lands in the rendered output.
            plain = "".join(_render_to_text(r) for r in _block_renderables(app.shown_view))
            assert "My Dashboard" in plain
            assert "billed" in plain and "$45.00" in plain
            assert "all clear" in plain

    asyncio.run(body())


# ---------------------------------------------------------------------------
# record_browser: shows master rows; moving the cursor updates the detail pane
# ---------------------------------------------------------------------------
def test_record_browser_master_and_detail_update():
    rows = [
        {"name": "alpha", "score": "1"},
        {"name": "bravo", "score": "2"},
        {"name": "charlie", "score": "3"},
    ]
    columns = ["name", "score"]

    def detail(row: dict) -> View:
        return View(f"Detail: {row['name']}", "", [Note(f"score is {row['score']}")])

    async def body():
        from textual.widgets import DataTable

        app = _BrowserApp_factory(rows=rows, columns=columns, detail=detail, title="t")
        async with app.run_test() as pilot:
            await pilot.pause()
            table = app.query_one("#master", DataTable)
            assert table.row_count == 3

            # Initial selection -> first row's detail View.
            assert app.detail_view.title == "Detail: alpha"
            first = "".join(_render_to_text(r) for r in _block_renderables(app.detail_view))
            assert "Detail: alpha" in first and "score is 1" in first

            # Move the cursor down -> detail re-renders for the next row.
            await pilot.press("down")
            await pilot.pause()
            assert app.detail_view.title == "Detail: bravo"
            second = "".join(_render_to_text(r) for r in _block_renderables(app.detail_view))
            assert "Detail: bravo" in second and "score is 2" in second

    asyncio.run(body())


# ---------------------------------------------------------------------------
# record_browser: filtering narrows the master table
# ---------------------------------------------------------------------------
def test_record_browser_filter_narrows_rows():
    rows = [
        {"name": "alpha", "score": "1"},
        {"name": "bravo", "score": "2"},
        {"name": "charlie", "score": "3"},
    ]

    def detail(row: dict) -> View:
        return View(row["name"], "", [Note(row["score"])])

    async def body():
        from textual.widgets import DataTable

        app = _BrowserApp_factory(rows=rows, columns=["name", "score"], detail=detail)
        async with app.run_test() as pilot:
            await pilot.pause()
            table = app.query_one("#master", DataTable)
            assert table.row_count == 3
            app._apply_filter("char")
            await pilot.pause()
            assert table.row_count == 1

    asyncio.run(body())


# ---------------------------------------------------------------------------
# Public API smoke + block renderables
# ---------------------------------------------------------------------------
def test_public_renderers_are_callable():
    assert callable(render_textual)
    assert callable(record_browser)


def test_block_renderables_includes_header_and_blocks():
    view = View("Title", "Sub", [Note("hello note")])
    renderables = _block_renderables(view)
    # header group + one note panel
    assert len(renderables) == 2
    plain = "".join(_render_to_text(r) for r in renderables)
    assert "Title" in plain and "Sub" in plain and "hello note" in plain


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _render_to_text(renderable) -> str:
    """Render a Rich renderable to a plain string for assertions."""
    from rich.console import Console

    buf = io.StringIO()
    Console(file=buf, force_terminal=False, width=200).print(renderable)
    return buf.getvalue()
