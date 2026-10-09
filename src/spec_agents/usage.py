"""Anthropic API cost computation — single source of truth for pricing.

Library-mode (per the v2 charter): this module is a pure pricing function
plus the canonical price table. It does no I/O, holds no state, and makes
no API calls. Callers that want stateful tracking (ledgers, budgets) build
that on top — see the script-internal `UsageTracker` in spectacular, which
is the candidate for a future `spec_agents.usage.UsageTracker` lift once a
second consumer needs it.

Why this exists: the token->USD formula and the per-model price table were
duplicated across ≥5 call sites in the stack. The Opus 4.7 -> 4.8 pricing
change caused stale numbers to ship because one copy was missed. Keep the
*one thing that changes* — prices — in exactly one place.

Update `PRICING_USD_PER_MTOK` when Anthropic changes prices. The canonical
human-readable source is the operator's memory entry `reference_model_tiers`.

Verification dates differ by row: the pre-5.5 rows were verified 2026-05-30; the
three 5.5 rows (Opus, Sonnet, Haiku) were read 2026-10-09 (each row says so).
Not representable by this signature: 1h cache writes, Batch API, fast mode and
the US data-residency 1.1x multiplier.

The prompt-length threshold is per request: Haiku 5.5 bills every token of a
request whose prompt exceeds 100,000 tokens at the long-prompt rates
(:data:`LONG_PROMPT_PRICING_USD_PER_MTOK`). Pass ONE request's tokens to
:func:`model_cost_usd`; never a sum over several calls.
"""

from __future__ import annotations

from typing import Final

# Per-MTok pricing. Rows other than the three 5.5 rows were verified against the live
# API rate card 2026-05-30; the 5.5 rows were read 2026-10-09 (each row cites it)
# (platform.claude.com/docs/en/about-claude/pricing). Cache multipliers per
# Anthropic's model: 5m cache_creation = 1.25× input; cache_read = 0.1× input,
# except where a row says otherwise.
PRICING_USD_PER_MTOK: Final[dict[str, dict[str, float]]] = {
    "claude-opus-4-8": {
        "input": 5.0,
        "output": 25.0,
        "cache_creation": 6.25,
        "cache_read": 0.50,
    },
    "claude-opus-4-7": {
        # Repriced to $5/$25 (matches 4.8) per the 2026-05-30 rate card;
        # was $15/$75 at launch.
        "input": 5.0,
        "output": 25.0,
        "cache_creation": 6.25,
        "cache_read": 0.50,
    },
    "claude-sonnet-4-6": {
        "input": 3.0,
        "output": 15.0,
        "cache_creation": 3.75,
        "cache_read": 0.30,
    },
    "claude-haiku-4-5-20251001": {
        # Haiku 4.5 = $1/$5 (NOT the retired Haiku 3.5's $0.80/$4 — the prior
        # table had 3.5's numbers mislabeled). Verified 2026-05-30.
        "input": 1.0,
        "output": 5.0,
        "cache_creation": 1.25,
        "cache_read": 0.10,
    },
    "claude-opus-5": {
        "input": 5.0,
        "output": 25.0,
        "cache_creation": 6.25,
        "cache_read": 0.50,
    },
    "claude-sonnet-5": {
        # Cheaper than claude-sonnet-4-6 ($2/$10 vs $3/$15) — do not assume
        # monotonically increasing price with model generation.
        "input": 2.0,
        "output": 10.0,
        "cache_creation": 2.50,
        "cache_read": 0.20,
    },
    "claude-fable-5-1": {
        "input": 10.0,
        "output": 50.0,
        "cache_creation": 12.50,
        # flat rate, NOT the module's stated 0.1x-input rule (line 25) — 0.1x
        # of Fable's $10 input would be $1.00, overstating the real rate 4x.
        "cache_read": 0.25,
    },
    "claude-opus-5-5": {
        # platform.claude.com/docs/en/about-claude/pricing, read 2026-10-09.
        # cache_read is the published flat $0.20 (0.05x input), NOT 0.1x ($0.40).
        "input": 4.0,
        "output": 20.0,
        "cache_creation": 5.0,
        "cache_read": 0.20,
    },
    "claude-sonnet-5-5": {
        # platform.claude.com/docs/en/about-claude/pricing, read 2026-10-09.
        # cache_read is the published flat $0.10 (0.05x input), NOT 0.1x ($0.20).
        "input": 2.0,
        "output": 10.0,
        "cache_creation": 2.50,
        "cache_read": 0.10,
    },
    "claude-haiku-5-5": {
        # platform.claude.com/docs/en/about-claude/pricing, read 2026-10-09.
        # Base rates, for a request whose prompt is <= 100,000 tokens; above that
        # see LONG_PROMPT_PRICING_USD_PER_MTOK.
        "input": 0.10,
        "output": 0.50,
        "cache_creation": 0.125,
        "cache_read": 0.01,
    },
}

# Models priced by prompt length (platform.claude.com/docs/en/about-claude/pricing,
# read 2026-10-09). A request whose prompt (input + cache creation + cache read
# tokens; output does not count) is strictly over the threshold is billed at the
# long rates for ALL of its tokens. Only Haiku 5.5 has a threshold.
LONG_PROMPT_THRESHOLD_TOKENS: Final[dict[str, int]] = {
    "claude-haiku-5-5": 100_000,
}
LONG_PROMPT_PRICING_USD_PER_MTOK: Final[dict[str, dict[str, float]]] = {
    "claude-haiku-5-5": {
        "input": 0.50,
        "output": 2.50,
        "cache_creation": 0.625,
        "cache_read": 0.05,
    },
}


def model_cost_usd(
    model: str,
    input_tokens: int,
    output_tokens: int,
    *,
    cache_creation_tokens: int = 0,
    cache_read_tokens: int = 0,
) -> float:
    """Return the USD cost of ONE Anthropic API request.

    The token arguments are one request's usage, not a sum over several: models
    with a prompt-length threshold (Haiku 5.5) are priced per request.

    Pure function: ``(input·price_in + output·price_out +
    cache_creation·price_cc + cache_read·price_cr) / 1_000_000``, using the
    per-MTok rates in :data:`PRICING_USD_PER_MTOK`.

    Raises ``KeyError`` if ``model`` is not in the pricing table. This is a
    deliberate, catchable signal — callers that prefer to record unknown
    models at zero cost (e.g. a usage ledger) should catch it explicitly
    rather than rely on a silent $0, which hides typos in model names.
    """
    prices = PRICING_USD_PER_MTOK[model]
    threshold = LONG_PROMPT_THRESHOLD_TOKENS.get(model)
    if (
        threshold is not None
        and input_tokens + cache_creation_tokens + cache_read_tokens > threshold
    ):
        prices = LONG_PROMPT_PRICING_USD_PER_MTOK[model]
    return (
        input_tokens * prices["input"]
        + output_tokens * prices["output"]
        + cache_creation_tokens * prices["cache_creation"]
        + cache_read_tokens * prices["cache_read"]
    ) / 1_000_000.0
