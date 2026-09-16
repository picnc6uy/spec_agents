# Pathfinder print → standalone card printer with an 80s interface — plan

**Status:** draft for operator review · **Date:** 2026-09-16 · **Branch:**
`claude/pathfinder-card-engine-ux-p2ag63`

Supersedes the earlier game-engine plan on this branch, which was written on a wrong
premise. Reviewed by the `Plan` subagent per `.agent/lenses/planning.md`; all findings
were accepted and folded in (Python launcher instead of `file://`, Chromium-only print,
structural condensation as the AI replacement, print spike before P0, backs deferred).

---

## 0. Verified vs. assumed

Operator confirmed: "Pathfinder print" is a project that prints Pathfinder cards. It is
not in `spec_agents` nor in any repo this session can reach, so this plan is written
without seeing the code. Everything marked **(revisit)** is re-estimated once the repo
is attached.

Assumptions (all decision-gated in §9):

- **A1.** Python, and it currently uses an AI call for at least one of: condensing card
  text to fit a card, normalising scraped data, choosing icons. "No AI" means every one
  of those becomes deterministic code or an editable field. Legacy AI-written text is
  **kept** as data; no new generation, at runtime or build time.
- **A2.** Cards are Pathfinder 2e reference cards (spells, items, feats, conditions,
  actions), poker size 63×88 mm, printed 3×3 on Letter or A4 and cut by hand.
- **A3.** Output today is a PDF or images; the pain points are text fit, layout, and a
  clunky workflow. The operator wants a tool they can open and use in 30 seconds.

## 1. Goals (operator-stated)

1. Runs on the PC. No AI, no network, no keys.
2. Fun 80s UI. The obvious homage is Brøderbund's *The Print Shop* (1984): a menu-driven
   wizard, SELECT → LAYOUT → PREVIEW → PRINT, dot-matrix noises.
3. Modern capability underneath: search, filters, saved sets, undo, print calibration.
4. Portability: runs on any PC with minimal setup.

## 2. The one design rule

**Retro on screen, crisp on paper.** The app chrome is 8-bit; the printed card is a
clean vector layout with real typography. Two render targets, one data model. Retro
card *backs* are an option, off by default.

## 3. Forced moves

1. **Print spike, before anything else, no repo needed.** A static HTML page with a 3×3
   grid of 63×88 mm boxes and a 100 mm ruler, printed on the operator's actual printer at
   scale 100%. One hour. It validates the whole technology choice (§4) and the
   calibration approach. A first version ships with this plan as `print-spike.html`.
2. **Attach the repo.** P0 cannot start until the code is visible.
3. **Data licensing shapes releases.** Foundry-derived card text and pack icons are not
   covered by an attribution page for public redistribution. Releases ship the app
   without card data; the importer runs on the user's machine.

## 4. Architecture

```
pfp_data      card records (JSON) + schema + importer(s). Python, build-time only.
              Parses Foundry HTML descriptions into SECTIONS (traits, cast, area,
              degrees of success, heightened…) and strips @UUID/@Damage enrichers.
pfp_layout    fit-to-card + card template + sheet imposition. JS/CSS, deterministic.
              Input: card record + template + paper preset. Output: printable DOM.
pfp_app       UI (library, set builder, preview, print wizard) + Storage.
pfp.py        ~20-line launcher: python -m http.server on localhost + open browser.
```

**Fit-to-card, in priority order (this is the AI replacement):**

1. **Operator `short_text`** wins when present. Legacy AI summaries land here in P0.
2. **Structural condensation**: drop or collapse sections by priority. Collapse
   Heightened entries to one line, drop tradition/trait lines already shown as tags,
   always keep degrees of success. Most cards fit at this step.
3. **Field-scoped abbreviations** from a fixed dictionary, never inside names.
4. **Shrink font** in steps to a floor of 7 pt (6.5 pt is marginal on a home inkjet).
5. **Continuation card** "(2/2)" breaking at a section boundary, header repeated.
   Never silently truncate.

## 5. Technology choice

| Option | Print fidelity | Retro UI | Portability | Fit with existing Python |
|---|---|---|---|---|
| **Local web app + Python launcher** | **best**: CSS `@page`, mm units, the browser's print engine handles every printer | easy: bitmap font, CSS palette | Python 3 + Chromium, which the operator already has; no install | Python remains the importer |
| Python + pygame-ce UI + fpdf2 | text wrapping and hyphenation are yours to write | full control | PyInstaller per OS | native |
| Python + Qt (PySide6) | good (QPrinter) | fighting the toolkit to look 8-bit | PyInstaller, 100 MB+ bundles | native |
| Textual TUI | none (must shell out) | terminal-bound | needs a terminal | native |

**Recommendation: local web app served by a tiny Python launcher.** Printing is the
core job, and CSS print layout plus the browser's print dialog is the best portable
print engine available. Honest cost line: **requires Python and Chromium; print is
Chromium-only.** A single-file inlined HTML build is a fallback for machines without
Python, not the product.

Print constraints to design against from day one:

- `file://` is not a target: Chrome blocks module scripts and JSON fetches there, and
  IndexedDB on `file://` is unreliable. The launcher exists for this reason.
- `@page { margin: 0 }` with padding inside the printable area, or Chrome adds a URL
  and date header. `print-color-adjust: exact` or backgrounds vanish.
- `@page size` is ignored by Safari and recent in Firefox. Chromium only, stated in
  the README.
- User-selected "fit to page" defeats calibration. The calibration page says
  "scale 100%" in large type.
- PDF export is the dialog's "Save as PDF". No dialog-free PDF in v1; weasyprint is the
  Python escape hatch if that grates.
- The browser cannot set duplex, and feed skew (X/Y offset) matters more than scale
  for backs. **v1 backs are a uniform, borderless pattern that tolerates offset.**
  Mirrored, aligned backs are v1.1 (§9).

## 6. The 80s look, concretely

- 16-colour EGA-ish palette, 8×8 bitmap font (Press Start 2P, OFL) for chrome, a
  legible pixel font at larger size for lists and content. CRT scanline toggle. Boot
  screen. One "INSERT DISK" joke, not ten.
- The Print Shop wizard: four big menu screens driven by arrow keys and Enter; mouse
  works everywhere. A one-line hint bar at the bottom of every screen. **The wizard
  structure and key navigation are built in P2 as infrastructure; P3 only skins it.**
- Dot-matrix sound while the print job builds, a tractor-feed progress bar, a
  "PRINT COMPLETE" chime. All sounds pre-baked WAV, all optional.
- Preview shows the real card render (crisp) inside a pixel frame, so what you see is
  what prints.

## 7. Modern layer

- Library: instant fuzzy search, filters by type/level/traits/source, keyboard-first.
- Set builder: add/remove/reorder, quantities, undo/redo as a snapshot stack. Sets
  saved in IndexedDB and exportable as JSON.
- Print: Letter and A4, poker size only at v1, cut marks, calibration page that prints
  a 100 mm ruler and a corner mark so the user enters measured scale **and** offset.
  "Print only cards I have not printed yet", marked on explicit confirm, not on
  `afterprint` (which fires on cancel).
- Offline: bundled fonts, no CDN, nothing fetched from the network.

## 8. Phases

| # | Phase | Cost | Definition of done |
|---|---|---|---|
| S | **Print spike** (§3.1) | 1 hour | printed boxes measure 63×88 mm ±0.5 at scale 100% on the operator's printer |
| P0 | **See the code, extract data** — attach repo, inventory what the AI did, card schema, importer that parses sections and strips enrichers, legacy summaries preserved as `short_text` | 1 sprint **(revisit)** | importer runs offline on the operator's full list; every AI-produced field is regenerated by code or kept as editable `short_text` |
| P1 | **Print core** — card template in CSS, fit-to-card pipeline (§4), imposition, cut marks, calibration page, build step that inlines data and fonts | 1–1.5 sprints | printed, cut cards measure 63×88 mm ±0.5; zero truncated cards across the operator's curated list; continuation cards only where structural condensation cannot fit |
| P2 | **App UX** — library, search, set builder, preview, wizard structure with placeholder CSS, launcher | 1–2 sprints | operator goes from launch to printed set in under 2 minutes without docs |
| P3 | **Retro skin** — palette, fonts, chrome, sounds, CRT toggle | 1 sprint, time-boxed | screenshot pass approved; per-card layout snapshot (font size, line count, overflow flag) identical before and after |
| P4 | **Release automation** — zipped build on tag, README with Chromium and scale-100% notes; data excluded | 0.5 sprint | fresh Windows/macOS/Linux machine with Python and Chrome runs the launcher, imports, prints a set |
| P5 | **Use & tune** | until exit | v1.0 = three real print runs with an empty "what annoyed me" list |

Total ≈ 5–7 two-week sprints at 1.5 contributors. Order rationale: the spike proves the
technology for an hour's work; P0 is the forced move; P1 before UX because a printer
that cannot fit text has no reason to have a pretty face; P3 skins only, so the wizard
is built once.

Repo discipline: `AGENTS.md` gates code changes behind a task spec. Each phase is one
`agent-task new` spec with its definition of done as acceptance criteria. The game
belongs in its own repo, not `spec_agents` (§9.2).

## 9. Decision-gated (recommendation in bold)

1. **Attach the repo** (owner/name), or push it somewhere Claude can read. Everything
   in P0 depends on it.
2. **Where the tool lives.** **A new repo** (`pathfinder_print`), since `spec_agents`
   is a domain-agnostic library and the tool must not depend on it.
3. **Web app + launcher vs. all-Python.** **Web app.**
4. **Card data source**: curated list vs. importer from the open Foundry VTT pf2e
   packs with your overrides layered on top. **Importer + overrides.**
5. **Action glyphs** (one/two/three-action, reaction, free): bundled glyph font vs.
   own SVGs. Licensing of the common glyph font is unclear. **Own SVGs**, four shapes.
6. **Backs**: v1 uniform pattern; mirrored aligned backs in v1.1 after calibration
   offset proves reliable. **Defer.**
7. **Retro card back** as an option. **Yes**, cheap, off by default.
8. **Whole-library fit check** (a headless Playwright harness measuring ~10k Foundry
   cards, ~2 days) vs. checking only the curated list. **Curated list at v1.**

## 10. Out of scope

- Any new AI generation, at runtime or build time, including "just to summarise".
  Legacy AI-written summaries are retained as data.
- Card art or pack icon images; art pipeline of any kind.
- Bridge, mini and tarot sizes; bleed; mirrored aligned backs (v1.1).
- Dialog-free PDF export; Tauri or any desktop wrapper; PWA install.
- Online sync, accounts, sharing.
- Rules automation of any kind; this prints references, it does not play.
- Localisation, a template designer UI (templates are CSS files), mobile,
  accessibility beyond keyboard-first and colour-blind-safe chrome.

## 11. Risks

- The existing project's value is mostly in AI-written summaries → P0 preserves them
  as `short_text`; nothing is lost when the AI is removed.
- Structural condensation misjudges a section priority → priorities live in one
  table per card type and are tuned in P5 against real prints.
- Print dialogs differ per OS/printer; scale and offset drift → calibration page.
- Bitmap font readability → pixel font only for chrome, larger legible font for content.
- Licensing → releases exclude data; importer runs locally; attribution page for
  ORC/OGL text.
