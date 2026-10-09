---
id: sa-prices-55-1
title: Price the three 5.5 models (Opus, Sonnet, Haiku) in spec_agents.usage
type: new-feature
lens: new-feature
created: 2026-10-09
status: drafted
budget:
  max_iterations: 40
  max_cost_usd: 6
  on_breach: abort-to-needs-rework
acceptance:
  - "P1 (rates). model_cost_usd prices claude-opus-5-5, claude-sonnet-5-5 and claude-haiku-5-5 (no date suffix) at the published rates below, for input, output, cache write (5m) and cache read; a test per model computes the cost of a mixed call by hand from these numbers and asserts equality to 1e-12. Opus 5.5: in 4.0, out 20.0, cache write 5.0, cache read 0.20. Sonnet 5.5: in 2.0, out 10.0, cache write 2.50, cache read 0.10. Haiku 5.5 (prompt up to 100,000 tokens): in 0.10, out 0.50, cache write 0.125, cache read 0.01."
  - "P2 (cache read is 0.05x, not 0.1x). The Opus 5.5 and Sonnet 5.5 cache-read rates are the published flat figures (0.20 and 0.10), not 0.1x input (which would be 0.40 and 0.20); a test fails if either is 0.1x input. The row comments say so, as the Fable 5.1 row does."
  - "P3 (citation). Each of the three rows carries a comment citing platform.claude.com/docs/en/about-claude/pricing and the date read (2026-10-09 by the spec author; the builder re-reads the page and, if a rate differs, uses the page and records the difference in the verification doc). Module docstring and the comment above the table no longer imply the 2026-05-30 verification date covers the new rows."
  - "P4 (Haiku 5.5 long prompt is modelled). A single Haiku 5.5 request whose prompt length (input_tokens + cache_creation_tokens + cache_read_tokens; the pricing page counts cache reads and writes toward the threshold) is over 100,000 is billed at the long-prompt rates for ALL its tokens: in 0.50, out 2.50, cache write 0.625, cache read 0.05. A request of exactly 100,000 prompt tokens is billed at the base rates. Tests pin: 100,000 (base), 100,001 (long), a prompt over the threshold made mostly of cache reads (long), and output tokens not counting toward the threshold. Opus 5.5, Sonnet 5.5 and every older model have no threshold: a 900k-token prompt costs the same per token as a 9k one (a test asserts it for both 5.5 models)."
  - "P5 (the threshold is per request, and map_agent respects it). model_cost_usd's token arguments are documented as ONE request. agents.parallel.map_agent today sums tokens over all calls and prices the sum once, which would bill a Haiku 5.5 fan-out of many short calls at the 5x long-prompt rate. After the change map_agent's cost_usd equals the sum of the per-call model_cost_usd values; a test with a fake client running Haiku 5.5 on several calls, each under 100,000 prompt tokens but summing over 100,000, asserts the base rate, and a second test with one call over the threshold asserts the long rate for that call only. The MapUsage totals fields are unchanged."
  - "P6 (nothing else moves). Every pre-existing row (claude-opus-4-8, claude-opus-4-7, claude-sonnet-4-6, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5, claude-fable-5-1) has values identical to origin/master, pinned by a test that compares each row, key by key, to literal expected numbers; model_cost_usd on an unknown model (gpt-4o, and an undated or misspelled 5.5 id such as claude-haiku-5-5-20260101) still raises KeyError; the function's keyword names are unchanged; the existing cases in test_usage.py, test_parallel.py and test_budget.py pass unmodified except where P5 adds a case."
  - "P7 (unchanged contract). The module stays pure: no I/O, no network, no state. DEFAULT_PARALLEL_MODEL stays claude-haiku-4-5-20251001 (switching defaults is model-pins-55-1 and the operator's call, not this card's)."
files:
  touched:
    - src/spec_agents/usage.py
    - src/spec_agents/agents/parallel.py
    - tests/test_usage.py
    - tests/test_parallel.py
    - tests/test_budget.py
    - docs/CURRENT_STATE.md
    - .agent/tasks/sa-prices-55-1.md
    - .agent/verifications/sa-prices-55-1.md
    # No changes/ directory exists in spec_agents (git ls-files changes is empty), so the brief's
    # "changes/ note" is met by the CURRENT_STATE.md pricing entry and the verification doc.
    # Test callers found by grepping tests/ for model_cost_usd, PRICING_USD_PER_MTOK, spec_agents.usage:
    # test_usage.py (table and function, directly), test_parallel.py (map_agent cost_usd, haiku-4-5 expected
    # value near line 229-240), test_budget.py (calls parallel.map_agent near line 264; must still pass).
  callers-unchanged:
    - src/spec_agents/__init__.py: docstring mention only; no code uses the table
    - src/spec_agents/agents/__init__.py: docstring mention of spec_agents.usage only
    - src/spec_agents/caching.py: docstring mention only; it does not import usage
    - AGENTS.md: names the usage surface; the surface (names, signature) is unchanged
  must-not-touch:
    - the KeyError behaviour of model_cost_usd (keep it, per the card)
    - the values of any existing price row
    - the package version in pyproject.toml and any release tag
    - the planning repo and its queue, ~/.claude and every settings file
---

# sa-prices-55-1: price the 5.5 models

Tree measured: `C:/Users/ghendrick/spec_agents--sa-prices-55-1`, `git log -1 --oneline` = `1c4dfb8 Merge pull request #1 from picnc6uy/agent/spec-agents-budget-1`, branch `agent/sa-prices-55-1`.

## Why
`spec_agents.usage.PRICING_USD_PER_MTOK` is the stack's only price table and has no row for any 5.5 model, so `model_cost_usd` raises `KeyError` for them. The stack is moving its pins to 5.5 (model-pins-55-1 depends on this card) and needs every pinned id priced first. The KeyError on an unknown model is deliberate and stays.

## What
Add three rows with the rates in P1, each citing the pricing page and read date. Three facts from the page (read 2026-10-09) shape the design:
1. Opus 5.5 and Sonnet 5.5 cache reads are 0.05x input (page footnote 2), not the usual 0.1x.
2. Haiku 5.5 is priced by prompt length: over 100,000 tokens, all of that request's tokens are billed at the long rates (in 0.50 / out 2.50 / 5m write 0.625 / read 0.05). Prompt length counts input, cache reads and cache writes; each request is priced on its own. Haiku 5.5 is the only model with a threshold.
3. Because the threshold is per request, a function fed summed tokens cannot price Haiku 5.5 correctly. `map_agent` sums over calls today (parallel.py near line 170); P5 requires per-call pricing. How the long-prompt rates are stored (second table, nested key, helper) is the builder's choice, provided the old rows keep their shape (`test_pricing_table_has_all_current_tiers` reads the four keys).

Update docs/CURRENT_STATE.md's pricing entry to list the new ids and the per-request rule. The verification doc records the page re-read, test counts before and after, and any rate difference found.

## Out of scope
- Changing DEFAULT_PARALLEL_MODEL or any other model pin (model-pins-55-1).
- 1h cache-write rates, Batch API, fast mode, and the US data-residency 1.1x multiplier (not representable by the current signature; the module docstring says so).
- Rows for models the card does not name (Fable 5, Mythos, Opus 4.x variants).
- The planning scripts' own price tables (token_use.py, cost_reconcile.py).

## Notes
- The 2026-10-07 cross-check from the brief matches the page read 2026-10-09: Opus 5.5 $4/$20 read $0.20; Sonnet 5.5 $2/$10 read $0.10; Haiku 5.5 $0.10/$0.50 read $0.01, x5 above 100k.
- Haiku 5.5 5m write rates ($0.125 base, $0.625 long) come from the same page table (1.25x input).
- Python: C:/Users/ghendrick/AppData/Local/Programs/Python/Python312/python.exe; one python process at a time.

## References
- https://platform.claude.com/docs/en/about-claude/pricing (read 2026-10-09)
- planning/agent-task/queue.toml, id sa-prices-55-1
- .agent/tasks/crs2-pricing-and-cache-doc-1.md (prior row-adding card, same test style)
