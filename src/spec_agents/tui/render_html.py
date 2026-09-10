"""Render a :class:`~spec_agents.tui.blocks.View` to a self-contained HTML page.

OFFLINE by construction: inline CSS only, no external/CDN ``src=``/``href=``, no
``<script>``. The page opens straight from disk. All dynamic text is
HTML-escaped. The CSS + DOM structure are ported verbatim from cost_reconcile's
v0 so existing cost dashboards keep their look (and their tests pass).
"""

from __future__ import annotations

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


def _esc(s: object) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# Ported verbatim from cost_reconcile.py v0 so the cost dashboard is unchanged.
# NOTE: no `█` glyph here — bars are CSS width:% only (offline, no glyph deps).
_HTML_CSS = """<style>
:root{--bg:#0f1117;--panel:#171a23;--ink:#e6e8ee;--muted:#8b93a7;--line:#262b38;
--track:#0c0e14;--cache:#4f7cff;--cachew:#7aa0ff;--output:#37d399;--warn:#ff5c7a;
--mono:'SFMono-Regular',Consolas,Menlo,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,
BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;line-height:1.5;padding:30px 22px}
.wrap{max-width:900px;margin:0 auto}
h1{font-size:20px;margin:0 0 2px}
.sub{color:var(--muted);font-size:13px;margin-bottom:18px}
.badges{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:24px}
.badge{background:var(--panel);border:1px solid var(--line);border-radius:999px;
padding:8px 14px;font-family:var(--mono);font-size:13px;display:flex;gap:8px;
align-items:center}
.badge b{font-size:14px}
.badge .t{color:var(--muted);font-size:11px;text-transform:uppercase;
letter-spacing:.5px}
.badge.bad b{color:var(--warn)}.badge.good b{color:var(--output)}
.badge.warn b{color:var(--cachew)}
section{background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:18px 18px 8px;margin-bottom:16px}
section.hero{border-color:#33406b}
section h2{font-size:14px;margin:0 0 4px;font-weight:600}
section .cap{color:var(--muted);font-size:12px;margin:0 0 14px}
.row{display:grid;grid-template-columns:170px 1fr 96px;align-items:center;
gap:10px;margin-bottom:10px}
.row .lbl{font-family:var(--mono);font-size:12px;color:var(--muted);
white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar{height:20px;border-radius:6px;background:var(--track);overflow:hidden}
.fill{height:100%;border-radius:6px}
.val{font-family:var(--mono);font-size:12px;text-align:right}
.note{font-family:var(--mono);font-size:12px;margin:0}
.note.bad{color:var(--warn)}.note.good{color:var(--output)}
.note.warn{color:var(--cachew)}
.tbl{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:12px}
.tbl th{text-align:left;color:var(--muted);font-weight:600;padding:4px 8px;
border-bottom:1px solid var(--line)}
.tbl td{padding:4px 8px;border-bottom:1px solid var(--line)}
.tbl td.num,.tbl th.num{text-align:right}
footer{color:var(--muted);font-size:12px;margin-top:16px;text-align:center}
</style>"""


def render_html(view: View) -> str:
    """Render ``view`` as a self-contained, offline HTML string."""
    body: list[str] = []
    body.append(f"<h1>{_esc(view.title)}</h1>")
    if view.subtitle:
        body.append(f'<div class="sub">{_esc(view.subtitle)}</div>')

    for block in view.blocks:
        if isinstance(block, Badges):
            body.append(_html_badges(block))
        elif isinstance(block, BarTable):
            body.append(_html_bartable(block))
        elif isinstance(block, Note):
            body.append(_html_note(block))
        elif isinstance(block, Table):
            body.append(_html_table(block))

    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{_esc(view.title)}</title>\n"
        f"{_HTML_CSS}\n"
        '</head><body><div class="wrap">\n' + "\n".join(body) + "\n</div></body></html>\n"
    )


def _html_badges(block: Badges) -> str:
    chips: list[str] = []
    for badge in block.items:
        cls = tone(badge.tone).html_class
        chips.append(
            f'<div class="badge {cls}"><span class="t">{_esc(badge.label)}</span>'
            f"<b>{_esc(badge.value)}</b></div>"
        )
    return '<div class="badges">\n' + "\n".join(chips) + "\n</div>"


def _html_bartable(block: BarTable) -> str:
    rows = block.sorted_rows()
    default_color = bar_color(block.color).html_color
    hero = ' class="hero"' if block.color == "accent" else ""
    out = [f"<section{hero}><h2>{_esc(block.title)}</h2>"]
    if not rows:
        out.append('<p class="cap">(none)</p>')
        out.append("</section>")
        return "\n".join(out)
    mx = max((r.value for r in rows), default=1.0) or 1.0
    for row in rows:
        w = max(0.0, row.value / mx * 100.0)
        color = tone(row.tone).html_color if row.tone else default_color
        out.append(
            f'<div class="row"><div class="lbl">{_esc(row.label)}</div>'
            f'<div class="bar"><div class="fill" style="width:{w:.1f}%;'
            f'background:{color}"></div></div>'
            f'<div class="val">{_esc(format_value(row.value, block.unit))}</div></div>'
        )
    out.append("</section>")
    return "\n".join(out)


def _html_note(block: Note) -> str:
    cls = tone(block.tone).html_class
    title = f"<h2>{_esc(block.title)}</h2>\n" if block.title else ""
    return f'<section>{title}<p class="note {cls}">{_esc(block.text)}</p></section>'


def _html_table(block: Table) -> str:
    head = "".join(
        f'<th class="{"num" if i else ""}">{_esc(c)}</th>' for i, c in enumerate(block.columns)
    )
    body_rows: list[str] = []
    for row in block.rows:
        cells = "".join(
            f'<td class="{"num" if i else ""}">{_esc(c)}</td>' for i, c in enumerate(row)
        )
        body_rows.append(f"<tr>{cells}</tr>")
    return (
        f"<section><h2>{_esc(block.title)}</h2>\n"
        f'<table class="tbl"><thead><tr>{head}</tr></thead>'
        f"<tbody>{''.join(body_rows)}</tbody></table>"
        "</section>"
    )
