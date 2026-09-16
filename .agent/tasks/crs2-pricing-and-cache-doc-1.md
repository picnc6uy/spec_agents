---
id: crs2-pricing-and-cache-doc-1
title: Add missing current-tier pricing rows and rename the misleading "cross-tier caching" docstring
type: bug-fix
lens: bug-fix
created: 2026-09-15
status: drafted
budget:
  # Soft caps the agent self-applies. On breach, do NOT grind on or fake green:
  # follow the escape-hatch contract in agent-task/RECOVERY.md.
  max_iterations: 20
  max_cost_usd: 2   # unit tests only; no live API call anywhere in this sprint
  on_breach: abort-to-needs-rework   # write needs-rework + reason; never silently continue
acceptance:
  - "A1 — Pricing rows added: `PRICING_USD_PER_MTOK` (src/spec_agents/usage.py:26) gains exactly three new keys — `claude-opus-5` (input 5.0, output 25.0, cache_creation 6.25, cache_read 0.50), `claude-sonnet-5` (input 2.0, output 10.0, cache_creation 2.50, cache_read 0.20), `claude-fable-5-1` (input 10.0, output 50.0, cache_creation 12.50, cache_read 0.25). No existing key's values change."
  - "A2 — Fable flat cache_read documented: the `claude-fable-5-1` entry's `cache_read: 0.25` is annotated with an inline comment stating that Fable's cache_read is a FLAT rate, NOT 0.1x its input price (0.1x would be $1.00), and that this deviates from the module-level 0.1x-input rule stated in the comment at line 25. Grep for the comment: `grep -n 'flat' src/spec_agents/usage.py` must return a hit inside or immediately above the `claude-fable-5-1` block."
  - "A3 — New pricing test file/section proves arithmetic, not just non-raising: for each of the three new models, a test calls `model_cost_usd` with distinct nonzero `input_tokens`, `output_tokens`, `cache_creation_tokens`, `cache_read_tokens` and asserts the exact expected float via `pytest.approx`, computed by hand from the stated per-MTok rates (e.g. opus-5 at 2_000_000 input + 1_000_000 output = $10 + $25 = $35). At least one test additionally isolates cache_read alone for `claude-fable-5-1` at a token count where the flat-vs-0.1x rates diverge (e.g. 1_000_000 cache_read tokens → $0.25, explicitly NOT $1.00) and asserts against the flat value."
  - "A4 — Sonnet-5-cheaper-than-Sonnet-4-6 is asserted directly: a test computes `model_cost_usd('claude-sonnet-5', ...)` and `model_cost_usd('claude-sonnet-4-6', ...)` on the identical token counts and asserts the sonnet-5 result is strictly less than the sonnet-4-6 result — guarding against a future edit that 'normalizes' newer-is-pricier."
  - "A5 — Unknown-model contract unchanged: an existing or new test calls `model_cost_usd` with a model string absent from the table (e.g. `'gpt-4o'`) and asserts `pytest.raises(KeyError)`; `model_cost_usd`'s body and docstring in usage.py are otherwise untouched by this sprint (diff-verified: no line changes inside the function other than the table it reads from)."
  - "A6 — `parallel.py:88` docstring renamed and corrected: the heading reads a cross-lens/same-tier framing (not \"Cross-tier caching\"), the example uses two calls at the SAME model with different preambles (e.g. two lenses over one corpus), and the prose states explicitly that Anthropic prompt caches are model-scoped — a cache written by one model cannot be read by a call at a different model — so a cheap-then-expensive tier split will NOT share the cache. The in-code comment at parallel.py:129 referencing the old heading is updated to match the new heading text."
  - "A7 — No other docstring/prose in the repo repeats the corrected claim under the old name: `grep -ri \"cross-tier\"` across the repo (excluding `.agent/tasks/code-review-swarm.md` and `.agent/verifications/code-review-swarm.md`, which are frozen historical records of a prior, separately-closed sprint and are explicitly out of scope — see Out of scope) returns zero hits, OR every remaining hit is inspected and confirmed not to assert cross-model cache sharing. `docs/CURRENT_STATE.md:72`'s \"the cross-tier / shared-lens cases\" phrasing and the two `tests/test_parallel.py` comments/docstring at lines ~159, ~184 (\"cross-tier caching\", \"cross-tier cache invariant\") are corrected to the cross-lens/same-tier framing, since they describe the same behavior as the parallel.py docstring, not a distinct historical claim."
  - "A8 — No behavioral change: `git diff` shows zero changes to `map_agent`'s executable code (the `if cached_prefix_text is None: ... else: ...` block and everything below it in parallel.py) — only the docstring text and the one inline comment at :129 change. All existing tests in `tests/test_parallel.py` and `tests/test_usage.py` pass unmodified in assertions (comment-only edits are permitted per A7)."
  - "A9 — Full test suite green: `pytest -q` passes with a strictly higher collected-test count than the pre-sprint baseline (record the baseline count in the verification doc before touching any file)."
  - "A10 — The referenced `planning/ideas/code-review-swarm-v2.spec.yaml` was searched for and not found anywhere on disk (verified via repo-wide grep/find before this spec was written); the verification doc records this and states that the rates above were sourced from the queue brief text directly, cross-checked against the operator's `reference_model_tiers` memory entry where available, not from the missing spec file. This is a documentation gap in a prior sprint's provenance trail, not something to fix here."
files:
  touched:
    - src/spec_agents/usage.py
    - tests/test_usage.py
    - src/spec_agents/agents/parallel.py
    - tests/test_parallel.py
    - docs/CURRENT_STATE.md
    - .agent/tasks/crs2-pricing-and-cache-doc-1.md
    - .agent/verifications/crs2-pricing-and-cache-doc-1.md
  must-not-touch:
    - src/spec_agents/agents/critic.py       # lens_first / cache_lenses logic is untouched; no claim in this sprint concerns critique()
    - src/spec_agents/caching.py             # cached_text_block mechanism unchanged
    - src/spec_agents/eval/                  # unrelated band
    - .agent/tasks/code-review-swarm.md      # frozen historical record of the already-closed sprint A; do not retroactively edit
    - .agent/verifications/code-review-swarm.md  # same — historical record, not live docs
    - map_agent's executable code in parallel.py (the system-block construction and everything below it) — docstring/comment text only
    - pyproject.toml                          # no public API changes; no version bump warranted
---

# crs2-pricing-and-cache-doc-1: pricing-table gap + misleading cache-scope docstring

## Why
Two independently-verified defects currently ship. `PRICING_USD_PER_MTOK` has zero
entries for the three models actually in use today (`claude-opus-5`,
`claude-sonnet-5`, `claude-fable-5-1`), so `model_cost_usd` — whose own docstring
calls its `KeyError` "deliberate" for genuinely unknown models — now raises on
every real cost rollup, not just typos. Separately, `parallel.py`'s
`cached_prefix_text` docstring is headed "Cross-tier caching" and illustrates it
with a cheap-tier breadth pass feeding an expensive-tier confirm pass sharing one
cache — but Anthropic prompt caches are scoped per model, so that exact usage
pattern silently pays full corpus price on the expensive call every time. Both
defects are cheap to fix and expensive to leave: one breaks cost accounting today,
the other actively misleads a future caller into an expensive mistake with no
error to catch it.

## What
**Defect A (pricing table).** Add three keys to `PRICING_USD_PER_MTOK` in
`src/spec_agents/usage.py`: `claude-opus-5` ($5/$25, cache_creation $6.25,
cache_read $0.50), `claude-sonnet-5` ($2/$10, cache_creation $2.50, cache_read
$0.20), `claude-fable-5-1` ($10/$50, cache_creation $12.50, cache_read $0.25 —
flat, not the module's stated 0.1x-input rule; comment this explicitly next to
the value). Do not touch `model_cost_usd`'s body, its docstring, or any existing
table entry. Add tests to `tests/test_usage.py` that compute exact expected
dollar amounts by hand for each new model (mirroring the existing
`test_known_model_input_output_cost` / `test_cache_tokens_are_priced` shape), one
test isolating Fable's flat cache_read against the 0.1x value it is NOT, one test
asserting sonnet-5 < sonnet-4-6 on identical inputs, and confirm the existing
`test_unknown_model_raises_keyerror` still passes untouched.

**Defect B (docstring).** In `src/spec_agents/agents/parallel.py`, rename the
`**Cross-tier caching**` heading at line 88 to a cross-lens/same-tier framing,
replace the "breadth pass and a confirm pass" example with two same-model calls
(e.g. two different reviewer lenses over one corpus, both at the same model),
and add an explicit sentence: Anthropic prompt caches are model-scoped, so a
cache written by one model's call cannot be read by a different model's call —
do not use this pattern to share a cache between tiers. Update the inline
comment at line 129 that cross-references the old heading name. Then grep the
repo for `cross-tier` (case-insensitive) and correct every live-docs hit that
makes the same claim: `docs/CURRENT_STATE.md:72` and the two `cross-tier`
references in `tests/test_parallel.py` (a docstring and a comment, not an
assertion — the test itself already proves same-model reuse, so only the prose
needs the same renaming). Historical, closed-sprint records
(`.agent/tasks/code-review-swarm.md`, `.agent/verifications/code-review-swarm.md`)
are explicitly excluded — see Out of scope.

## Out of scope
- Fixing `map_agent`'s or `critique`'s actual behavior. Neither function assumes
  cross-model cache reuse today (P5 in the brief) — this sprint only corrects
  wording that implied they could be *used* that way. If exploration turns up an
  actual code path that assumes cross-model reuse, stop, do not fix it, and
  report it as a separate finding in the verification doc.
- Editing `.agent/tasks/code-review-swarm.md` or
  `.agent/verifications/code-review-swarm.md`. These are the frozen record of
  a prior, already-closed sprint. Their `cross-tier` language describes what
  that sprint believed at the time; rewriting history there would falsify the
  record. Correct only the *currently live* docs and docstrings.
- Recreating `planning/ideas/code-review-swarm-v2.spec.yaml`. It is referenced
  by the queue brief and does not exist on disk (confirmed by repo-wide search
  before this spec was written). Reconstructing it is a separate task; this
  sprint sources its numbers directly from the queue brief text instead. Note
  the gap in the verification doc; do not silently author a replacement file.
- Any version bump or `CHANGELOG`/`CURRENT_STATE.md` "Now" entry beyond the
  `cross-tier` wording fix at line 72. This is a table correction and a
  docstring correction, not a new feature — no public API changed shape.
- `critic.py`'s `lens_first` mechanism, `caching.py`, and anything under
  `src/spec_agents/eval/`.

## Notes
- **Gotcha 1 (Fable flat cache_read):** applying the module's stated "cache_read
  = 0.1x input" rule to Fable ($10 input) gives $1.00, overstating Fable's real
  $0.25 flat cache_read rate by 4x. The comment must be visible enough that
  editing the table under time pressure doesn't "fix" it back to 0.1x.
- **Gotcha 2 (sonnet-5 cheaper than sonnet-4-6):** $2/$10 vs the existing
  $3/$15 — resist any instinct to assume monotonically increasing price with
  model generation; test it directly (A4) rather than trusting a comment.
- **The referenced spec.yaml does not exist.** `planning/ideas/code-review-swarm-v2.spec.yaml`
  was searched for repo-wide (glob + `find`) and not found in this worktree, the
  `spec_agents` main checkout, or the `planning` working directory. The brief's
  numbers are taken directly from the queue entry text; cross-check against the
  operator's `reference_model_tiers` memory entry if available in the executing
  session, but do not block on the missing file — it is a provenance gap to
  flag, not a blocker to this sprint's acceptance criteria.
- Per the bug-fix lens: write the reproduction first (a test asserting
  `model_cost_usd("claude-opus-5", ...)` currently raises `KeyError` on
  unmodified code / a docstring-content assertion for parallel.py), confirm it
  fails on `master`, then fix, then confirm it passes. Note in the verification
  doc whether existing test coverage should have caught the missing rows sooner
  (it should have — `test_pricing_table_has_all_current_tiers` in
  `tests/test_usage.py` hardcodes the three OLD model names rather than
  deriving them from any "currently supported" source, so it silently missed
  the gap; consider recommending, as a backlog note only, a coverage rule tying
  that test's model list to whatever the codebase treats as "current").

## References
- `src/spec_agents/usage.py` — module docstring (:1-17), `PRICING_USD_PER_MTOK` (:26-55),
  `model_cost_usd` (:58-83).
- `src/spec_agents/agents/parallel.py:80-135` — `map_agent` docstring and the
  `cached_prefix_text` system-block construction.
- `tests/test_usage.py`, `tests/test_parallel.py:159-198` — existing test shapes
  to extend/correct.
- `docs/CURRENT_STATE.md:70-84` — the "code-review-swarm sprint A" landing note
  containing the other live `cross-tier` phrasing.
- `.agent/tasks/code-review-swarm.md`, `.agent/verifications/code-review-swarm.md`
  — historical record of the sprint that introduced `cached_prefix_text`; read
  for context, do not edit.
- `.agent/lenses/bug-fix.md` — reproduce-first discipline this spec follows.
- Queue brief: `planning/agent-task/queue.toml`, `[[sprint]] id =
  "crs2-pricing-and-cache-doc-1"` (source of the rates and the two gotchas
  above, in the absence of the referenced spec.yaml).
