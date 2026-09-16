# pathfinder-print → a fun, standalone, AI-free desktop tool — plan

**Status:** draft v3 for operator review · **Date:** 2026-09-16 · **Branch:**
`claude/pathfinder-card-engine-ux-p2ag63` (spec_agents) · **Target repo:** `pathfinder-print`

This version is written against the real code (`picnc6uy/pathfinder-print` @ `b9101bc`,
attached 2026-09-16). It supersedes the two earlier drafts on this branch, which were
written blind. Its intended final home is `pathfinder-print/PLAN.md` (the canonical
authority for that repo); §11 is the amendment text, ready to apply once the operator says
where the plan lives.

---

## 1. Scope

- **Repo:** `pathfinder-print` only. `spec_agents` is not touched (the tool is stdlib-only
  by design and not a kernel consumer).
- **Horizon:** 4–5 sprints, sequenced after the two Lane 1 sprints that are still queued
  (`planning/sprints/2026-09-13-four-lane-plan.md` §5): `pp-parse-gold-1`,
  `pp-render-1`, `pp-print-packet-1`. `pp-conftest-1` and the import work (as `pp-db-2`)
  have shipped.
- **Altitude:** operational (UX + packaging). No methodology change; the sprint loop,
  task specs, `changes/` fragments and the four gates apply unchanged.

## 2. What exists (verified, not assumed)

| Piece | State | Relevant to this plan |
|---|---|---|
| `web/deck.html` + `deck.js` (632 lines) | v1.2 shipped. Runs from `file://` or as the extension page. Auto-fit 10→7 pt, overflow front→back→continuation (P-7), summary mode (P-9), Section 15 footer (P-8), profiles `index-4x6` and `letter-2up-4x6`, duplex with mirrored backs, **calibration page already built** | the renderer is the crisp-on-paper half; it stays byte-for-byte |
| `web/browse.html` + `browse.js` | shipped (pp-browse-1). Search + 4 facets + add-all over `web/data/*.json.gz`. **Needs `http://`** (`fetch()` cannot read `file://`); today the operator runs `python -m http.server` by hand | the "modern capability" half already exists; it lacks a front door |
| `web/clipper/` (MV3 extension) | shipped. "Add to card deck" on d20pfsrd pages; writes to `chrome.storage.local` | a data source, not the product (P-1). **Its deck store is separate from the localStorage deck** a served page uses |
| `src/pathfinder_print/` | stdlib-only core: profiles, corpus shaping, OGL verifier, eval + improve-loop mechanics | untouched by this plan |
| `tools/import_spells.py` → `data/pfp.sqlite` → `tools/export_index.py` → `web/data/` | 623 spells, byte-stable rebuild; source IMarvinTPA CSV is `redistributable: true` with Section 15 pinned | `web/data/` and `data/sources/` are gitignored, so a fresh checkout has **no corpus** |
| AI surface | `tools/summarize.py` (optional `llm` extra, **never run live**); `improve_loop.py` has no real generator, and the lane plan explicitly refuses to fund one | "no AI" is already true of the product path; only the deck page's hint text and the extra advertise it |
| Tests | 172 static, Playwright-driven page tests, CI green on `main` | every UI change needs a page test; `PFP.deck.faces()` is the layout snapshot surface |
| Printed cards to date | **zero** (lane plan §5, CURRENT_STATE "Next") | the forced move |

Could not verify here: the test suite (this container has Python 3.11; the project requires
3.12). CI on `main` is the evidence instead.

## 3. What the operator asked for, translated

| Ask | What it means against this code |
|---|---|
| "use it directly on my PC" | one double-click opens the tool with the corpus loaded. Today it is three entry points (extension, `file://` page, hand-run `http.server`) and a gitignored data build |
| "no AI involvement" | the product path never imports `anthropic`; summaries stay operator-written (P-9 already allows this); the summarize hint leaves the UI |
| "fun UX, 80s video game interface" | retro **on screen only**: a Print Shop-style wizard with keyboard navigation, palette, bitmap font, sounds. The printed card is unchanged |
| "modern capability" | keep search/facets/add-all/calibration/duplex; add undo, named decks, keyboard-first navigation |
| "portability" | a zip that runs on any Windows PC with Python 3.12 and Chrome; a no-Python bundle is decision-gated |

## 4. The one design rule

**Retro on screen, crisp on paper.** Every retro rule lives under `@media screen`; the
`@media print` block and the card CSS stay untouched, and a test asserts
`PFP.deck.faces()` (font size, text, overflow flag per face) is identical before and after
each UI sprint. The wizard is chrome around the existing renderer, never a second renderer.

## 5. Forced moves

1. **Print one sheet.** `deck.html` already has the calibration page and the 4x6 profile.
   `pp-print-packet-1` is queued to make this a 15-minute packet. Nothing in this plan is
   worth doing if 4x6 cards do not come out of the operator's printer at the right size.
   Cost: 15 minutes of operator time. Cost of skipping: every sprint below builds on an
   unmeasured print path.
2. **The two-deck problem.** A page served on `http://localhost` keeps its deck in
   `localStorage`; the clipper writes to `chrome.storage.local`. The wizard will not see
   clipped cards unless the operator exports from the extension's deck page and imports.
   v1 of the wizard accepts that (import exists); a `POST /add` bridge in the launcher is
   decision-gated (§9.4). Not planning around this would ship a wizard that "loses" clips.
3. **Corpus on a fresh checkout.** The launcher must either build `web/data/` (importer +
   exporter) or ship it. Decision-gated (§9.2) but must be settled before `pp-portable-1`.

## 6. Sprints, in order

Each is one task spec in `.agent/tasks/`, light tier unless noted, with a `changes/`
fragment at close. `files.touched` is sketched so the operator can see blast radius.

| # | id | type · cost | The bite | Definition of done |
|---|---|---|---|---|
| 1 | `pp-launcher-1` | new-feature · 0.5 sprint | `pfp.py` at repo root, stdlib only: serve `web/` on an ephemeral localhost port, open the default browser at `web/index.html` (a one-screen hub linking browse → deck → print for now). If `web/data/index-spell.json.gz` is missing and `data/sources/imarvintpa_spells.csv` is present, run the importer and exporter first; if the CSV is missing, print the one fetch instruction and stop. `run.bat` for Windows using the absolute 3.12 interpreter from AGENTS.md. Touches: `pfp.py`, `run.bat`, `web/index.html`, `tests/test_launcher.py`, docs | double-click → browser opens on the hub with 623 spells searchable; no extension, no hand-run server; `python pfp.py --check` exits 0 on a fresh clone with the CSV present |
| 2 | `pp-wizard-1` | new-feature · 1–2 sprints | The Print Shop structure, plain CSS: one page, four screens (SELECT = browse, DECK = list + summary editor, LAYOUT = profile/duplex/sides/calibration, PRINT = preview + print). A scene stack, one focus model driven by arrows/Enter/Esc **and** mouse, a hint bar on every screen. Undo/redo as a snapshot stack over `PFP.deck.state()`. Named decks (an index in localStorage; each deck still exports as `deck.json`, P-5). Calls the existing `PFP.deck.*` and browse modules; `paginate`/`impose`/`render` untouched. Touches: `web/index.html`, `web/wizard.js`, `web/wizard.css`, `web/browse.js` (module boundary only), `tests/test_wizard.py` | launch → printed set in under 2 minutes, once keyboard-only and once mouse-only; `faces()` snapshot identical to `main` for the sample deck; undo restores the exact prior state |
| 3 | `pp-noai-1` | chore · 0.25 sprint | Make the AI-free path the product path: drop the `tools/summarize.py` hint from the deck UI; move `summarize.py` and the `llm` extra under a `tools/optional/` note that says dev-only, or shelve them (§9.3); add a test that `web/` and `pfp.py` reference no host but `localhost` and `d20pfsrd.com`; amend P-9 wording. Touches: `web/deck.html`, `pyproject.toml`, `tools/`, `PLAN.md`, `tests/` | grep-clean test passes; PLAN.md P-9 says operator-written summaries are the product path |
| 4 | `pp-retro-1` | new-feature · 1 sprint, **time-boxed** | The skin. 16-colour palette as CSS tokens with themes (EGA default; CGA, C64, Game Boy swaps), an OFL bitmap font bundled under `web/fonts/` for chrome only, CRT scanline overlay toggle, boot screen with PRESS ENTER (also the audio-unlock gesture), pre-baked WAVs (dot-matrix while imposing, "PRINT COMPLETE" chime) committed as small files, tractor-feed progress bar. All under `@media screen`. Touches: `web/wizard.css`, `web/retro.js`, `web/fonts/`, `web/sfx/`, `tests/test_wizard.py` | screenshot pass approved by operator; `faces()` snapshot identical; sound off by default and never before the first keypress; every theme passes a contrast check on the hint bar |
| 5 | `pp-portable-1` | new-feature · 0.5–1 sprint | Release zip on tag: repo tree + `run.bat` + (per §9.2) the built spells corpus with its Section 15 notice. README states the two requirements, Python 3.12 and Chrome/Edge, and the print rule (100 %, never fit-to-page). A no-Python PyInstaller bundle only if §9.1 says so. Touches: `.github/workflows/release.yml`, `README.md`, `docs/` | a fresh Windows machine with Python 3.12 and Chrome unzips, double-clicks, prints the calibration page and one 4x6 card that measures within 0.5 mm |

Total ≈ 3.5–5 sprints after Lane 1. Order rationale: the launcher is the smallest change
that makes everything else usable and it is what `pp-print-packet-1` will want too; the
wizard is built once with plain CSS so the retro sprint only skins; the no-AI chore is
cheap and can ride between them; packaging last because it packages what exists.

## 7. Cross-cutting

- **Layout snapshot test.** One fixture deck (`docs/samples/deck-sleep-wish-planar-ally.json`
  exists) rendered through `faces()` and compared to a committed JSON. Introduced in sprint
  2, guards sprints 2, 4 and 5.
- **Vocabulary and discipline.** Planning's terms (operator, sprint, task spec,
  verification doc) and pathfinder-print's gates (pytest, ruff check, ruff format,
  `pyright --pythonpath <abs-3.12>`) apply to every sprint above.

## 8. Out of scope

- Any new AI generation, in the product or at build time, including a generator for
  `improve_loop.py` (already refused by the lane plan).
- A second renderer, PDF library, or any change to `paginate`/`impose`/card CSS.
- New print profiles (lane plan: stop designing profiles; `pp-render-1` adds the one MPC
  profile that enables an order).
- Retro styling of the printed card or the d20pfsrd clipper button.
- Monsters and magic items (blocked on a licensed bulk source, per `sources.manifest.json`).
- Accounts, sync, hosted anything (P-5). Firefox. A Web Store listing. Mobile.
- Localisation, a template designer, accessibility beyond keyboard-first and a
  colour-blind-safe default theme.

## 9. Decision-gated (recommendation in bold)

1. **Portability target.** Zip + Python 3.12 + Chrome (zero new deps) vs. a PyInstaller
   one-folder bundle that removes the Python requirement (adds a build matrix and antivirus
   false positives). **Zip first; bundle only if the tool is shared beyond the operator.**
2. **Ship the spells corpus?** `web/data/` is gitignored today. The source is
   `redistributable: true` with Section 15 pinned, and the rebuild is byte-stable, so
   committing the ~240 KB of `web/data/*.json.gz` with the notice is defensible.
   **Commit it**, so a fresh checkout and the zip both work with no fetch. Revisit if a
   non-redistributable source is ever enabled.
3. **`tools/summarize.py`.** Shelve (delete from the tree, keep in history) vs. keep as
   dev-only optional. **Keep, relabelled dev-only**, because P-9's provenance fields exist
   and it costs nothing while unused.
4. **Clipper bridge.** Have the extension `POST` records to the running launcher so clips
   land in the wizard's deck without export/import. Needs a localhost host permission in
   the manifest and a 30-line handler. **Defer to a later sprint**; measure how often the
   operator clips vs. browses first.
5. **Where this plan lives.** Apply §11 to `pathfinder-print/PLAN.md` on a branch there
   (needs the operator's go-ahead to push to that repo) vs. keep it here. **Apply it
   there**; PLAN.md is the declared single authority.
6. **Palette era.** EGA-16 default with swaps, vs. one fixed theme. **EGA-16 + swaps**;
   themes are one token table each.

## 10. Risks

- **A wizard that hides the renderer's honesty.** Overflow flags, `needs_review`, and
  truncated summaries must stay visible on the DECK screen; the retro skin cannot swallow
  warnings into decoration.
- **Browser print behaviour.** Chromium only (stated in README); `@page` rules are already
  injected per profile; user "fit to page" defeats calibration, so the PRINT screen shows
  the rule in large type.
- **Audio autoplay.** Browsers block sound before a gesture; the boot screen's PRESS
  ENTER is a requirement, not decoration.
- **Two decks.** §5.2; the DECK screen must say where clipped cards go until the bridge
  exists.
- **Scope creep in the retro sprint.** Time-boxed; extra juice goes to a later sprint only
  if the operator asks after using it.

## 11. PLAN.md amendment (ready to apply in pathfinder-print)

Add to §0 Decisions:

| ID | Decision | Date |
|---|---|---|
| P-10 | **The primary entry point is a local launcher** (`pfp.py` + `run.bat`) that serves `web/` on localhost and opens the browser. `file://` and the extension page remain supported but are not the front door. | 2026-09-16 |
| P-11 | **Retro on screen, crisp on paper.** The operator UI is an 80s-style wizard under `@media screen`; card CSS and `@media print` are unchanged, guarded by a `faces()` snapshot test. | 2026-09-16 |
| P-12 | **No AI in the product path.** `tools/summarize.py` and the `llm` extra are dev-only and optional; summaries in the product are operator-written (narrows P-9). | 2026-09-16 |

Add to §7 Phases, after v1.2:

> **v1.5 — desktop UX (The Print Shop).** `pp-launcher-1`, `pp-wizard-1`, `pp-noai-1`,
> `pp-retro-1`, `pp-portable-1` per the plan on the spec_agents branch
> `claude/pathfinder-card-engine-ux-p2ag63` (to be folded into this file). Sequenced after
> Lane 1's `pp-parse-gold-1`, `pp-render-1`, `pp-print-packet-1`.
