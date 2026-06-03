"""Tests for spec_agents.tui — the reusable terminal-UI kit.

One test per block path: badge tones, bar scaling + all three sort modes, the
$/count value formatter, Note + Table rendering, and the View header. The HTML
renderer is checked for the offline guarantees (doctype, escaping, no network /
no script / no src=). The Rich renderer is exercised into a recorded
StringIO Console so titles/labels land in the captured output.

Fully offline: no network, no spec_agents install needed (run with
PYTHONPATH=<repo>/src). Only `rich` is required for the render_rich tests.
"""

from __future__ import annotations

import io

import pytest

from spec_agents.tui import (
    Badge,
    Badges,
    BarRow,
    BarTable,
    Note,
    Table,
    View,
    format_value,
    render_html,
    render_rich,
    tone,
)
from spec_agents.tui.blocks import bar_color


# ---------------------------------------------------------------------------
# Tone vocabulary
# ---------------------------------------------------------------------------
def test_tone_resolves_known_and_defaults_neutral():
    assert tone("good").rich == "green"
    assert tone("bad").rich == "red"
    assert tone("warn").rich == "yellow"
    assert tone("neutral").rich == "cyan"
    # Unknown / None fall back to neutral.
    assert tone("nope").rich == "cyan"
    assert tone(None).rich == "cyan"


def test_bar_color_accent_aliases_neutral():
    assert bar_color("accent").rich == tone("neutral").rich
    assert bar_color("good").rich == "green"


# ---------------------------------------------------------------------------
# Value formatting ($ vs count)
# ---------------------------------------------------------------------------
def test_format_value_dollars():
    assert format_value(1234.5, "$") == "$1,234.50"
    assert format_value(0, "$") == "$0.00"


def test_format_value_count():
    assert format_value(1234.6, "") == "1,235"  # rounds, no decimals
    assert format_value(0, "") == "0"


# ---------------------------------------------------------------------------
# BarTable scaling + sort modes
# ---------------------------------------------------------------------------
def test_bartable_sort_value_descending_default():
    bt = BarTable("t", [BarRow("a", 1.0), BarRow("b", 9.0), BarRow("c", 5.0)])
    assert [r.label for r in bt.sorted_rows()] == ["b", "c", "a"]


def test_bartable_sort_label_ascending():
    bt = BarTable("t", [BarRow("c", 5.0), BarRow("a", 1.0), BarRow("b", 9.0)], sort="label")
    assert [r.label for r in bt.sorted_rows()] == ["a", "b", "c"]


def test_bartable_sort_none_keeps_order():
    bt = BarTable("t", [BarRow("c", 5.0), BarRow("a", 1.0)], sort="none")
    assert [r.label for r in bt.sorted_rows()] == ["c", "a"]


def test_bartable_bar_scaling_in_rich(recorded_console):
    # Max row fills the full 28-cell bar; a half-value row fills ~14.
    console, buf = recorded_console
    view = View(
        "Scale",
        "",
        [
            BarTable("Bars", [BarRow("max", 100.0), BarRow("half", 50.0)], unit="$"),
        ],
    )
    render_rich(view, console)
    out = buf.getvalue()
    assert out.count("█") >= 1  # bars rendered
    assert "$100.00" in out and "$50.00" in out


# ---------------------------------------------------------------------------
# Badges
# ---------------------------------------------------------------------------
def test_badges_render_rich_includes_label_and_value(recorded_console):
    console, buf = recorded_console
    view = View(
        "Hdr",
        "sub",
        [
            Badges(
                [Badge("billed", "$45.00", tone="bad"), Badge("carried", "$10.00", tone="good")]
            ),
        ],
    )
    render_rich(view, console)
    out = buf.getvalue()
    assert "billed" in out and "$45.00" in out
    assert "carried" in out and "$10.00" in out


def test_badges_render_html_tone_classes():
    view = View(
        "Hdr",
        "",
        [
            Badges(
                [Badge("billed", "$45.00", tone="bad"), Badge("carried", "$10.00", tone="good")]
            ),
        ],
    )
    html = render_html(view)
    assert 'class="badge bad"' in html
    assert 'class="badge good"' in html
    assert "$45.00" in html and "$10.00" in html


# ---------------------------------------------------------------------------
# Note + Table
# ---------------------------------------------------------------------------
def test_note_renders_rich_and_html():
    view = View("V", "", [Note("all clear", tone="good", title="Status")])
    html = render_html(view)
    assert "all clear" in html
    assert 'class="note good"' in html
    assert "Status" in html


def test_note_render_rich_text(recorded_console):
    console, buf = recorded_console
    render_rich(View("V", "", [Note("watch out", tone="warn")]), console)
    assert "watch out" in buf.getvalue()


def test_table_renders_rich_and_html(recorded_console):
    block = Table("Spend", ["Key", "USD"], [["key_a", "$15.00"], ["key_b", "$30.00"]])
    html = render_html(View("V", "", [block]))
    assert "Spend" in html and "key_a" in html and "$30.00" in html
    console, buf = recorded_console
    render_rich(View("V", "", [block]), console)
    out = buf.getvalue()
    assert "Spend" in out and "key_a" in out


# ---------------------------------------------------------------------------
# View header
# ---------------------------------------------------------------------------
def test_view_title_and_subtitle_render_rich(recorded_console):
    console, buf = recorded_console
    render_rich(View("My Dashboard", "the subtitle", []), console)
    out = buf.getvalue()
    assert "My Dashboard" in out
    assert "the subtitle" in out


# ---------------------------------------------------------------------------
# render_html: offline guarantees
# ---------------------------------------------------------------------------
def _sample_view():
    return View(
        "Cost",
        "window · offline",
        [
            Badges([Badge("billed", "$45.00", tone="bad")]),
            BarTable("Cost by usage type", [BarRow("input", 40.0), BarRow("output", 5.0)]),
            Note("No anomalies.", tone="good"),
        ],
    )


def test_render_html_starts_with_doctype():
    assert render_html(_sample_view()).startswith("<!doctype html")


def test_render_html_escapes_dynamic_text():
    view = View(
        "V",
        "",
        [
            BarTable("t", [BarRow("a<script>&b", 1.0)]),
        ],
    )
    html = render_html(view)
    assert "&lt;script&gt;&amp;" in html
    assert "<script>" not in html


def test_render_html_no_network_or_scripts():
    html = render_html(_sample_view())
    assert "http://" not in html
    assert "https://" not in html
    assert "src=" not in html
    assert "<script" not in html


# ---------------------------------------------------------------------------
# render_rich: titles/labels land in captured output
# ---------------------------------------------------------------------------
def test_render_rich_contains_titles_and_labels(recorded_console):
    console, buf = recorded_console
    render_rich(_sample_view(), console)
    out = buf.getvalue()
    assert "Cost" in out  # view title
    assert "Cost by usage type" in out  # bartable title
    assert "input" in out and "output" in out  # bar labels


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def recorded_console():
    pytest.importorskip("rich")
    from rich.console import Console

    buf = io.StringIO()
    console = Console(file=buf, force_terminal=True, width=120, record=True)
    return console, buf
