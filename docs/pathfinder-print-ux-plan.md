# pathfinder-print → a fun, standalone, AI-free desktop tool — plan

**Status:** v3.1, **executed and merged 2026-09-16** — all six sprints landed on `pathfinder-print`
`main` via PR #13 (rebase merge, head `23cc028`, CI green on the pushed SHA). The stacked branches
were:
`agent/pp-launcher-1` → `agent/pp-wizard-1` → `agent/pp-wizard-2` → `agent/pp-retro-1` →
`agent/pp-noai-1` → `agent/pp-portable-1`. Suite 183 → 246 tests, all four gates green on
every branch. Two operator follow-ups remain: commit the built corpus from the PC
(`python pfp.py --check`, then `git add web/data/*.json.gz`, P-13) and, after merging,
`git tag v0.2.0 && git push --tags` to publish the first zip. Original status line follows. · **Date:** 2026-09-16 · **Branch:**
`claude/pathfinder-card-engine-ux-p2ag63` (spec_agents) · **Target repo:** `pathfinder-print`

Written against the real code (`picnc6uy/pathfinder-print` @ `b9101bc`, attached
2026-09-16). Supersedes the two blind drafts on this branch. Reviewed once by the `Plan`
subagent with the repo in front of it; all findings accepted and folded in (fixed port and
on-disk deck persistence, staging must stay measurable, wizard split in two, retro sprint
cut down, corpus decision settled now, launcher unblocked from Lane 1). Its final home is
`pathfinder-print/PLAN.md`; §12 is the amendment text.

---

## 1. Scope

- **Repo:** `pathfinder-print` only. `spec_agents` is not touched.
- **Horizon:** 6 sprints, interleaved with the queued Lane 1 sprints
  (`planning/sprints/2026-09-13-four-lane-plan.md` §5: `pp-parse-gold-1`, `pp-render-1`,
  `pp-print-packet-1`; `pp-conftest-1` and the import work shipped).
- **Altitude:** operational (UX + packaging) with one methodology item (§8).

## 2. What exists (verified against the files)

| Piece | State | Bearing on this plan |
|---|---|---|
| `web/deck.html` + `deck.js` | v1.2. Runs from `file://` or as the extension page; storage is `chrome.storage.local` when the extension API exists, else `localStorage`. Auto-fit 10→7 pt, overflow front→back→continuation (P-7), summary mode (P-9), Section 15 footer (P-8), profiles `index-4x6` and `letter-2up-4x6`, duplex with mirrored backs, a calibration page, and a paste-HTML input that needs no extension | the renderer is the crisp-on-paper half and stays byte-for-byte. **Auto-fit measures `scrollHeight` in `#staging`; if any screen hides `#sheet`/`#staging` or an ancestor with `display:none`, every face "fits" at 10 pt** |
| `web/browse.html` + `browse.js` | search + 4 facets + add-all over `web/data/*.json.gz`; needs `http://`. Self-initialises on `PFP.deck.ready` against fixed element ids | the modern half exists but is a standalone page; embedding it means a small `init()` refactor, not a "boundary only" change |
| `web/clipper/` (MV3) | "Add to card deck" on d20pfsrd pages → `chrome.storage.local` | **sole source today for feats, rules sections, and the ~2,000 d20pfsrd spells outside the 623-row CSV.** Its store is separate from a served page's `localStorage` |
| `tests/test_web.py` | pins `PFP.PROFILES` to exactly the two browser-print profiles | if `pp-render-1` adds `mpc-photo` to `deck.js`, a LAYOUT screen must not list it (PNG-only, no print path) |
| Corpus | `tools/import_spells.py` → `data/pfp.sqlite` → `tools/export_index.py` → `web/data/` (~240 KB gz). Source CSV is `redistributable: true`, Section 15 pinned, rebuild byte-stable. `data/sources/`, `data/*.sqlite`, `web/data/` all gitignored; `export_index.py`'s docstring says "never committed" | a fresh clone has no corpus and cannot build one |
| AI surface | `tools/summarize.py` (optional `llm` extra, never run live); `improve_loop.py` has no generator and the lane plan refuses to fund one | "no AI" is already true of the product path |
| Printed cards | **zero** | the forced move |

Unverified here: the test suite (container has Python 3.11; project needs 3.12). CI green
on `main` stands in.

## 3. The ask, translated

| Ask | Meaning against this code |
|---|---|
| use it directly on my PC | one double-click, corpus loaded, deck persisted on disk. Today: three entry points and a gitignored data build |
| no AI involvement | the product path never imports `anthropic`; summaries are operator-written (P-9 already allows it); the summarize hint leaves the UI |
| fun 80s interface | retro on screen only: a Print Shop-style wizard with keyboard navigation, palette, bitmap font. Printed card unchanged |
| modern capability | keep search/facets/add-all/calibration/duplex; add undo and keyboard-first navigation |
| portability | a zip that runs on any Windows PC with Python 3.12 and Chrome; a no-Python bundle is decision-gated |

## 4. Two design rules

1. **Retro on screen, crisp on paper.** Retro rules live under `@media screen`; card CSS
   and `@media print` are untouched. `#staging` stays measurable on every screen (never
   `display:none` on it or an ancestor). A `faces()` snapshot test runs **against the
   wizard page**, not `deck.html`.
2. **The deck is a file (P-5), and the launcher owns it.** The served page keeps the deck
   in memory and `POST`s it to the launcher, which writes `deck.json` to disk. That is the
   persistence story, the fixed-origin story, and later the clipper bridge, in one ~30-line
   handler.

## 5. Forced moves

1. **Print one sheet.** `deck.html` already has the calibration page and the 4x6 profile;
   `pp-print-packet-1` makes it a 15-minute packet. It stays first. Cost of skipping: every
   sprint below builds on an unmeasured print path.
2. **Fixed origin.** An ephemeral port is a new origin every launch, so `localStorage`
   would vanish each time. The launcher uses a fixed default port (8765) with fallback
   plus a visible warning, and persists the deck to disk per rule 2 so the port does not
   matter for data.
3. **Corpus on a fresh clone. Decided now, not later:** commit the IMarvinTPA CSV
   (sha256 already pinned in `sources.manifest.json`) and the built `web/data/*.json.gz`,
   with `web/data/NOTICE` carrying the Section 15 text and `*.gz` marked binary in
   `.gitattributes`. Record it as P-13 and fix `export_index.py`'s docstring in the same
   sprint. `pp-print-packet-1` wants a corpus on disk too.
4. **The two-deck problem.** Clipped cards land in the extension's store, not the
   wizard's. Until the bridge exists (§10.4) the DECK screen says so and points at the two
   AI-free, extension-free inputs that already work: paste-HTML and `deck.json` import.

## 6. Sprints, in order

One task spec each in `.agent/tasks/`, a `changes/` fragment at close. Tier and
`files.touched` shown so blast radius and Lane 1 collisions are visible.

| # | id | tier · cost | The bite | Definition of done |
|---|---|---|---|---|
| 0 | `pp-print-packet-1` (queued, Lane 1) | as specified | first, unchanged | a measured 4x6 sheet |
| 1 | `pp-launcher-1` | light · 0.5 sprint | `pfp.py`, stdlib only: serve `web/` on port 8765 (fallback + warning), open the browser at `web/index.html` (a one-screen hub for now), `GET/POST /deck` reading and writing `deck.json` beside the launcher. `run.bat`: `py -3.12`, falling back to the absolute interpreter in AGENTS.md. No auto-build branch: the corpus is committed (§5.3). Touches: `pfp.py`, `run.bat`, `web/index.html`, `web/data/`, `data/sources/`, `.gitignore`, `.gitattributes`, `tools/export_index.py` (docstring), `tests/test_launcher.py`, `PLAN.md` (P-13) — disjoint from `pp-parse-gold-1` (`web/parse.js`) and `pp-render-1` (`tools/render.py`), so it can run alongside them | double-click → browser opens on the hub with 623 spells searchable; quit and relaunch → the deck is still there; `python pfp.py --check` exits 0 on a fresh clone |
| 2 | `pp-wizard-1` | **full** · 1 sprint | Screens + keyboard. One page, four screens (SELECT = browse, DECK = list + summary editor + warnings, LAYOUT = browser-print profiles only, duplex, sides, calibration, PRINT = preview + print), a scene stack, one focus model driven by arrows/Enter/Esc and mouse, a hint bar. Plain CSS. `browse.js` `init()` refactored to mount into a container. `paginate`/`impose`/`render` untouched; `#staging` measurable on every screen. New `faces()` snapshot test against `index.html` with `docs/samples/deck-sleep-wish-planar-ally.json`. Touches: `web/index.html`, `web/wizard.js`, `web/wizard.css`, `web/browse.js`, `tests/test_wizard.py`, `tests/fixtures/` | launch → printed set in under 2 minutes, once keyboard-only and once mouse-only; snapshot identical to `deck.html`'s output for the fixture deck |
| 3 | `pp-wizard-2` | full · 1 sprint | Undo/redo as a snapshot stack over `PFP.deck.state()`; "open recent" over `deck.json` files the launcher has seen (no named-deck index; P-5 says the file is the deck). Touches: `web/wizard.js`, `pfp.py`, `tests/` | undo restores the exact prior state through 20 mixed edits; open-recent round-trips |
| 4 | `pp-noai-1` | chore · 0.25 sprint, **after `pp-render-1` merges** (both touch `PLAN.md`) | Drop the `summarize.py` hint from `deck.html`; relabel `tools/summarize.py` + `llm` extra dev-only; test that `web/` and `pfp.py` reference no host but `localhost` and `d20pfsrd.com`; amend P-9. Touches: `web/deck.html`, `pyproject.toml`, `tools/summarize.py`, `PLAN.md`, `tests/` | grep test passes; PLAN.md P-12 recorded |
| 5 | `pp-retro-1` | light · 1 sprint, **time-boxed** | The skin, cut to what fits: one EGA-16 theme as CSS tokens, one OFL bitmap font under `web/fonts/` for chrome only, CRT scanline toggle, boot screen with PRESS ENTER. **Deferred:** theme swaps, audio, tractor-feed bar (§10.6). All under `@media screen`. Touches: `web/wizard.css`, `web/retro.js`, `web/fonts/`, `tests/test_wizard.py` | screenshot pass approved; `faces()` snapshot identical; hint bar passes a contrast check |
| 6 | `pp-portable-1` | light · 0.5 sprint | Release zip on tag: tree + `run.bat` + committed corpus + NOTICE. README states the two requirements (Python 3.12, Chrome/Edge) and the print rule (100 %, never fit-to-page). PyInstaller only if §10.1 says so. Touches: `.github/workflows/release.yml`, `README.md` | a fresh Windows machine with Python 3.12 and Chrome unzips, double-clicks, prints the calibration page and one 4x6 card within 0.5 mm |

Total ≈ 4.25 sprints of new work. Order rationale: the packet proves printing; the launcher
is small, disjoint from Lane 1, and gives every later sprint a front door and a fixed
origin; the wizard is built plain so the retro sprint only skins; the no-AI chore waits
for `pp-render-1` to avoid a `PLAN.md` collision; packaging last.

## 7. Cross-cutting

- **Layout snapshot gate.** Introduced in sprint 2 against `index.html`; guards 2, 3, 5, 6.
- **Discipline.** Planning vocabulary (operator, sprint, task spec, verification doc) and
  the four gates incl. `pyright --pythonpath <abs-3.12>` apply to every sprint.
- **SELECT serves spells only** until a licensed bulk source for monsters or items
  clears `sources.manifest.json`; the screen says so.

## 8. Methodology validation

The `faces()` snapshot is a reusable pattern: **a regression gate for UI-only sprints**,
proving that a change to chrome left the artifact byte-identical. If it holds across
sprints 2, 3, 5 and 6, it is a candidate for the stack's lens set (a "skin" sprint type).

## 9. Out of scope

- Any new AI generation, in the product or at build time, including a generator for
  `improve_loop.py`.
- A second renderer, a PDF library, or any change to `paginate`/`impose`/card CSS.
- New print profiles beyond Lane 1's `mpc-photo`; the LAYOUT screen never lists PNG-only
  profiles.
- Named decks (P-5 says the file is the deck); theme swaps, audio and the tractor-feed
  bar (deferred, §10.6); a launcher auto-build branch (the corpus is committed).
- Retro styling of the printed card or the clipper button.
- Monsters and magic items until a licensed bulk source exists.
- Accounts, sync, hosted anything (P-5). Firefox. A Web Store listing. Mobile.
  Localisation, a template designer, accessibility beyond keyboard-first and a
  colour-blind-safe default theme.

## 10. Decision-gated (recommendation in bold)

1. **Portability target.** Zip + Python 3.12 + Chrome vs. a PyInstaller bundle. **Zip
   first; bundle only if the tool is shared beyond the operator.**
2. **Commit the corpus and its CSV.** Set out in §5.3. **Yes**, recorded as P-13.
3. **`tools/summarize.py`.** Shelve vs. keep dev-only. **Keep, relabelled dev-only.**
4. **Clipper bridge.** The extension `POST`s records to the launcher (needs a localhost
   host permission in the manifest; the handler already exists from sprint 1). **Do it as
   `pp-bridge-1` right after `pp-wizard-2`** if the operator still clips feats or rules
   sections; until then paste-HTML and import cover it.
5. **Where this plan lives.** Apply §12 to `pathfinder-print/PLAN.md` on a branch there
   (needs the operator's go-ahead to push to that repo). **Apply it there.**
6. **Retro extras.** Theme swaps (CGA, C64, Game Boy), dot-matrix/chime audio,
   tractor-feed bar as a later `pp-retro-2`. **Only if the operator asks after using
   `pp-retro-1`.**

## 11. Risks

- **A wizard that hides the renderer's honesty.** Overflow flags, `needs_review`, and
  truncated summaries stay visible on DECK; the skin cannot swallow warnings.
- **Hidden staging.** Rule 4.1; the snapshot test is the tripwire.
- **Browser print.** Chromium only, stated in README; "fit to page" defeats calibration,
  so PRINT shows the rule in large type.
- **Two decks.** §5.4 until the bridge lands.
- **`PLAN.md` collisions** with Lane 1: only `pp-noai-1` touches it before `pp-render-1`
  merges, and it is held.

## 12. PLAN.md amendment (ready to apply in pathfinder-print)

Add to §0 Decisions:

| ID | Decision | Date |
|---|---|---|
| P-10 | **The primary entry point is a local launcher** (`pfp.py` + `run.bat`) serving `web/` on a fixed localhost port and persisting `deck.json` to disk via `POST /deck`. `file://` and the extension page remain supported but are not the front door. | 2026-09-16 |
| P-11 | **Retro on screen, crisp on paper.** The operator UI is an 80s-style wizard under `@media screen`; card CSS and `@media print` are unchanged; `#staging` stays measurable on every screen; a `faces()` snapshot test on the wizard page guards it. | 2026-09-16 |
| P-12 | **No AI in the product path.** `tools/summarize.py` and the `llm` extra are dev-only and optional; product summaries are operator-written (narrows P-9). | 2026-09-16 |
| P-13 | **The spells corpus is committed**: `data/sources/imarvintpa_spells.csv` (sha256 pinned in the manifest) and `web/data/*.json.gz`, with `web/data/NOTICE` carrying the Section 15 text. Supersedes the "never committed" note in `tools/export_index.py`. Revisit if a non-redistributable source is enabled. | 2026-09-16 |

Add to §7 Phases, after v1.2:

> **v1.5 — desktop UX (The Print Shop).** `pp-launcher-1`, `pp-wizard-1`, `pp-wizard-2`,
> `pp-noai-1`, `pp-retro-1`, `pp-portable-1`, per the plan on the spec_agents branch
> `claude/pathfinder-card-engine-ux-p2ag63` (to be folded into this file).
> `pp-print-packet-1` stays first; `pp-launcher-1` may run alongside `pp-parse-gold-1`
> and `pp-render-1`; `pp-noai-1` waits for `pp-render-1`.
