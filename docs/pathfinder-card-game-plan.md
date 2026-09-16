# Pathfinder card engine → standalone desktop game — plan

**Status:** draft for operator review · **Date:** 2026-09-16 · **Branch:**
`claude/pathfinder-card-engine-ux-p2ag63`

Independently reviewed by the `Plan` subagent per `.agent/lenses/planning.md`; all
review findings were accepted and folded in (undo barriers, storage abstraction,
licensing gate, packaging pulled forward, honest browser-build cost).

---

## 0. What was verified, and what is assumed

The Pathfinder card engine is **not** in `spec_agents`: no file, commit, branch or
history match for "pathfinder", "card" or "deck". The only other repo this session can
see (`PhotoProject`) is archived and unrelated. The engine most likely lives in
`spectacular`, `personal_os`, or only on the operator's PC. **Locating it is the first
forced move (§1).**

Assumptions this plan is written under (each is decision-gated in §8):

- **A1.** The engine is Python (everything else in the operator's stack is).
- **A2.** Its rules are Pathfinder Adventure Card Game-shaped: a player deck against an
  encounter/location deck, dice checks, hand/discard/bury/recharge zones. If it is
  something else, only the table layout in P2 changes.
- **A3.** "No AI involvement" means no LLM or API call at runtime and no `anthropic` or
  `spec_agents` import in the shipped game. Every decision the engine currently asks an
  agent to make becomes either a human choice (the player) or a fixed rule (the
  encounter side). Attract mode replays a recorded game; nothing "plays" on its own.

## 1. Forced moves (before any sprint starts)

1. **Locate and assess the engine** (operator, no engineering cost). Outcomes:
   - found, Python, rules separable from agent code → P0 as costed below;
   - found but rules and agent decisions are entangled → P0 doubles;
   - not found or unusable → **write the core from the rules**, 2–3 sprints, replacing P0.
2. **Content licensing.** If the cards and scenarios are Paizo's PACG text, a public
   web build and tagged GitHub releases distribute their IP, and the Community Use
   Policy does not cover a full playable reimplementation with card text. Decide
   *original content* vs. *PACG content* before P5 and before any public web build.
   Original content keeps every distribution option open; PACG content means private
   builds only.

## 2. Goals (operator-stated)

1. Runs directly on the PC. No network, no keys, no AI.
2. Fun UX with an 80s arcade / home-computer feel.
3. Modern capability underneath: undo, save anywhere, seeded runs, mouse + keyboard
   + gamepad, resizable window, accessibility options.
4. Portability: one download per OS, no installer, and a browser build if it stays cheap.

## 3. Architecture — three layers with a hard boundary

```
pathfinder_core     pure rules engine. No I/O, no clock, no third-party deps.
                    RNG injected and derived per decision: rng(seed, action_index).
                    State = plain dataclasses, JSON round-trippable.
                    API: legal_actions(state) -> [Action]
                         apply(state, action)  -> (state', [Event])
                    Event carries reveals_hidden_info: bool (drives undo barriers).
pathfinder_content  cards / decks / scenarios as JSON or TOML + a schema validator
                    (validator lives here, not in core, so core stays zero-dep).
                    Art referenced by id, never by path.
pathfinder_app      the game shell: scenes, input, renderer, audio, options, and a
                    Storage interface with desktop (platformdirs) and web
                    (IndexedDB via pygbag's platform.window) backends.
```

Why the boundary is the whole plan:

- **No AI.** The core has no hook where an agent could sit. Enforced by a test: after
  `import pathfinder_core`, `sys.modules` contains only stdlib and core modules.
- **Portability.** A pure core runs under CPython, PyInstaller and WebAssembly alike.
- **Fun.** Events (CardDrawn, CheckRolled, Crit, LocationClosed…) are what the shell
  animates and sounds. Without events the UI has nothing to "juice".
- **Testability.** Seed + action log fully determines a game, so replays are tests.
  UI randomness (screen shake, attract-mode variation) uses a separate RNG so the
  replay-determinism claim holds.

## 4. Technology choice

| Option | 80s look | Modern layer | Portability | Fit with a Python engine | Verdict |
|---|---|---|---|---|---|
| **pygame-ce** | full control: pixel canvas, palette, chiptune | all of it, **but you hand-roll the UI toolkit** (focus, layout, wrapping, tweens, scene stack) | PyInstaller for Win/mac/Linux, pygbag for browser | native | **recommended** |
| Godot 4 | best tooling | best, UI toolkit included | one-click exports incl. web | engine must be ported to GDScript/C# | only if the engine is tiny or must be rewritten anyway (§1, outcome 3) |
| TypeScript + PixiJS + Tauri | full control | all | web first, desktop via Tauri | engine must be ported | pick if the engine is already TS |
| Textual TUI (in spec_agents) | terminal-bound; no sound; font is the user's | no gamepad | needs a terminal | native | no; the headless CLI in P0 is the stepping stone instead |
| LÖVE (Lua) | full control | all | good | port required | no |

Recommendation: **pygame-ce**, with the main loop written `async` from day one so the
same code can run under pygbag. The named cost of this choice is the UI toolkit, which
is most of P2. If the forced move in §1 ends in "write the core from scratch", reopen
this decision: Godot's free UI toolkit then competes on equal footing.

Known browser-build (pygbag) constraints, so nobody designs against them by accident:

- Audio starts only after a user gesture. The PRESS START screen satisfies this; it is
  a requirement, not a flourish.
- Tracker modules (MOD/XM) are unreliable in pygbag's mixer. Music is OGG only.
- No filesystem persistence. Saves go through the `Storage` interface (§3).
- pygbag pins a specific CPython/pygame-ce pair and breaks on unrelated dependency
  bumps. Gamepad support in browsers is partial.
- numpy is a fragile wheel under pygbag and adds 30–60 MB to desktop bundles. It is
  **not** a runtime dependency (see §5, SFX).

## 5. The 80s look, concretely

- Internal canvas **384×216** (16:9, 8×8 tiles → 48×27 grid), integer-scaled with
  nearest-neighbour to the window, letterboxed. Everything is drawn at canvas
  resolution; the window can be any size.
- One enforced palette (16 colours, EGA-like) with swappable themes: CGA (4 colours,
  for laughs), C64, Game Boy green, "arcade" (NES-ish). Colour is a token, never a
  literal, so a theme is one table.
- 8×8 bitmap font (OFL-licensed, e.g. Press Start 2P) plus a 4×6 small variant. Titles
  all-caps. Text reveals character by character with a blip; Enter skips.
- CRT overlay, toggleable and cheap: scanline surface + vignette. No shader dependency.
  Barrel curvature only if it costs nothing in fps.
- **SFX are pre-baked to WAV by a build script** (square/triangle/noise synthesis in
  stdlib `array` or numpy *at build time only*). Runtime loads WAVs. No asset
  dependency before any art exists, and no numpy in the bundle.
- Tropes on purpose: attract-mode demo (a replay), PRESS START, three-initial high-score
  entry, STAGE CLEAR tally roll-up, screen flash + shake on a crit, CONTINUE? 9…0.
- **Deliberate break from the rule:** card text must be readable. Hover/focus on any
  card opens an inspect panel at a larger scale with full rules text. In-game rules
  reference lives behind one key. Fun is the frame; the game stays legible.

## 6. Modern layer

- **Undo with barriers.** Any action that reveals hidden information or resolves
  randomness (draw, reveal, die roll) is a commit point; undo cannot cross it. Between
  barriers undo is free: reorder plays, take back a blessing before the roll. This is
  the standard fix for the two failure modes of naive undo: deterministic redraw leaks
  the next card, and re-rolled redraw invites reroll abuse. An optional **practice mode**
  lifts the barriers and disables the high-score table and seeded-run code.
- **Save anywhere.** A save is `{seed, content_version, action_log}` plus a cached
  snapshot for fast load. Autosave after every action. Saves are tiny and diffable, and
  they go through `Storage` so desktop and web behave the same.
- **Seeded runs.** 8-character run code on the title screen; "daily" is date-derived.
- **Input.** Keyboard (arrows/WASD, Z/X/Enter/Esc), mouse (click, hover, optional drag),
  gamepad via SDL mappings. One focus model (a grid of focusable zones) drives all
  three, so nothing is mouse-only or keyboard-only. **Gamepad is built with the focus
  model in P2**, not retrofitted.
- **Options.** Palette theme, CRT on/off, integer vs. stretch scaling, SFX/music
  volume, text speed, animation speed with an "instant" setting, colour-blind-safe
  icons (shape + colour, never colour alone), export game log to text.
- Window: resizable, F11 fullscreen, remembers size and position. 60 fps on integrated
  graphics; start-up under 2 s.

## 7. Portability and packaging

- GitHub Actions matrix on every tag: PyInstaller **one-folder** zips for Windows and
  Linux, a `.app` zip for macOS. One-file builds are avoided (slow start, more antivirus
  false positives).
- macOS: `macos-latest` runners are arm64 only; Intel Macs need a second runner or a
  universal2 build. Since macOS 15, right-click → Open no longer bypasses unsigned
  apps; the README must point users to System Settings → Privacy & Security. Signing
  stays out of scope.
- Browser build via pygbag to GitHub Pages **only if §1 licensing allows public
  distribution**. Budget ~0.5 sprint plus recurring pin maintenance; it is nice-to-have
  with a kill switch, not a commitment.
- Saves and options in the platform user directory via `Storage`; assets loaded via
  `importlib.resources` so frozen and web builds find them the same way.
- Zero network: a test asserts no `socket` use during a full headless game.

## 8. Phases, each with a definition of done

| # | Phase | Cost | Definition of done |
|---|---|---|---|
| P0 | **Engine extraction** — move into `pathfinder_core`, delete AI and `spec_agents` deps, inject per-decision RNG, JSON state, action/event API with `reveals_hidden_info`, `Storage` interface, a headless text CLI that plays a full game | 1 sprint (×2 if entangled; 2–3 if written from scratch) | core imports nothing outside stdlib; 1,000 random playouts finish without exception; same seed + log ⇒ identical final state |
| P1 | **Vertical slice + first build** — pygame-ce async loop, one Table scene, rectangles and text only, full game playable; **CI produces a Windows zip that launches** | 1 sprint | operator finishes a game with mouse and with keyboard; ≥60 fps; the zip runs on a clean Windows machine |
| P2 | **Table UX** — UI toolkit (focus model, layout, wrapping, tweens, scene stack), zone layout, gamepad, inspect panel, in-game rules reference, event-driven animation, log panel, undo with barriers | 2–3 sprints | a new player finishes a game without external docs, once each with mouse, keyboard and gamepad |
| P3 | **Retro polish** — palette themes, bitmap font, CRT overlay, pre-baked SFX, OGG music, attract mode, high-score table | 1–2 sprints, **time-boxed** | every Event has a sound and a motion; screenshot pass approved by operator |
| P4 | **Modern layer** — saves, seeds, options screen, accessibility toggles, practice mode | 1 sprint | save mid-game, quit, relaunch, resume ⇒ identical state; undo never crosses a barrier outside practice mode |
| P5 | **Release process** — macOS and Linux builds, tagged releases, optional pygbag page | 1 sprint (+0.5 for web) | fresh Windows, macOS and Linux machines run the zip with no install; web build plays a full game if in scope |
| P6 | **Playtest & tune** | until exit | **v1.0 = three consecutive playtests with an empty "what annoyed me" list** |

Total: roughly 9–12 two-week sprints, i.e. **5–6 months at 1.5 contributors**, before
the engine is located. Order rationale: P0 is the forced move; P1 proves the engine
boundary is real and catches packaging failures while they are cheap; P3 is the fun but
the most expandable phase, so it is time-boxed and lands after the game is playable end
to end.

Repo discipline: `AGENTS.md` gates code changes behind a task spec. Each phase above is
one `agent-task new` spec with its definition of done as the acceptance criteria.

## 9. Decision-gated (recommendation in bold)

1. **Where is the engine, and in what language?** Python → this plan. TypeScript → same
   architecture, PixiJS + Tauri instead of pygame-ce. Nowhere → §1 outcome 3, and
   reopen Godot. **Point me at it.**
2. **Original content or PACG content?** **Original**, because it keeps public
   releases and the web build available. PACG content means private builds only.
3. **Which rules set?** PACG-style vs. a custom design. Affects P0 and the table layout
   in P2 only.
4. **Where does the game live?** **A new repo** (`pathfinder_card_game`). `spec_agents`
   is a domain-agnostic library whose hard deps include `anthropic`; the game must not
   depend on it or live inside it. This branch carries only this plan.
5. **Browser build in scope?** **Yes as nice-to-have**, gated on decision 2, costed at
   0.5 sprint plus maintenance, with a kill switch if it distorts the desktop design.
6. **Code signing?** **Defer.** Document the warnings; revisit if the game is shared
   beyond a few people.
7. **Era / palette?** **EGA-like 16 colours with theme swaps.** True-arcade colour
   depth loses the constraint that makes the look cohere.
8. **Placeholder art until P6, or commission pixel art earlier?** **Placeholders**
   (icon glyphs + coloured card frames); art is the easiest thing to add last.

## 10. Out of scope

- Any AI/LLM at runtime, in the build, or as an "opponent". Rule-driven only.
- Online multiplayer, accounts, leaderboards beyond the local high-score table.
- Mobile builds, Steam, code signing, installers.
- A card/scenario editor (content is data files; edit with a text editor).
- Localisation (strings live in one table so it is possible later, not planned).
- Porting the engine to another language for its own sake.
- Card-art production pipeline.
- A Textual/terminal version of the game.

## 11. Risks

- Engine entangled with agent decision points → P0 doubles. Mitigation: the headless
  CLI in P0 surfaces every decision point early.
- Content licensing blocks public distribution → decided in §1 before P5, not after.
- Font/music licensing → OFL fonts and self-synthesised SFX only; music is last.
- PyInstaller antivirus false positives → one-folder builds and documented warnings.
- pygbag pin breakage → web build is optional and has a kill switch.
- Polish scope creep → P3 time-boxed; P6 is where extra juice goes, deliberately.
