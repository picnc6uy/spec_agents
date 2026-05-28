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
"""

from __future__ import annotations

from typing import Final

# Per-MTok pricing as of 2026-05-28 (Opus 4.8 release).
# Cache multipliers follow Anthropic's documented model:
#   cache_creation ≈ 1.25× input price; cache_read ≈ 0.1× input price.
PRICING_USD_PER_MTOK: Final[dict[str, dict[str, float]]] = {
    "claude-opus-4-8": {
        "input": 5.0,
        "output": 25.0,
        "cache_creation": 6.25,
        "cache_read": 0.50,
    },
    "claude-opus-4-7": {
        "input": 15.0,
        "output": 75.0,
        "cache_creation": 18.75,
        "cache_read": 1.50,
    },
    "claude-sonnet-4-6": {
        "input": 3.0,
        "output": 15.0,
        "cache_creation": 3.75,
        "cache_read": 0.30,
    },
    "claude-haiku-4-5-20251001": {
        "input": 0.80,
        "output": 4.0,
        "cache_creation": 1.0,
        "cache_read": 0.08,
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
    """Return the USD cost of one Anthropic API call.

    Pure function: ``(input·price_in + output·price_out +
    cache_creation·price_cc + cache_read·price_cr) / 1_000_000``, using the
    per-MTok rates in :data:`PRICING_USD_PER_MTOK`.

    Raises ``KeyError`` if ``model`` is not in the pricing table. This is a
    deliberate, catchable signal — callers that prefer to record unknown
    models at zero cost (e.g. a usage ledger) should catch it explicitly
    rather than rely on a silent $0, which hides typos in model names.
    """
    prices = PRICING_USD_PER_MTOK[model]
    return (
        input_tokens * prices["input"]
        + output_tokens * prices["output"]
        + cache_creation_tokens * prices["cache_creation"]
        + cache_read_tokens * prices["cache_read"]
    ) / 1_000_000.0
