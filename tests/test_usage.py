"""Smoke tests for spec_agents.usage (single-source pricing)."""

from __future__ import annotations

import pytest

from spec_agents.usage import PRICING_USD_PER_MTOK, model_cost_usd


def test_known_model_input_output_cost() -> None:
    # 1M input + 1M output on Opus 4.8 = $5 + $25 = $30.
    cost = model_cost_usd("claude-opus-4-8", 1_000_000, 1_000_000)
    assert cost == pytest.approx(30.0)


def test_sonnet_cost_differs_from_opus() -> None:
    # 1M input + 1M output on Sonnet 4.6 = $3 + $15 = $18.
    cost = model_cost_usd("claude-sonnet-4-6", 1_000_000, 1_000_000)
    assert cost == pytest.approx(18.0)


def test_cache_tokens_are_priced() -> None:
    # 1M cache_creation + 1M cache_read on Opus 4.8 = $6.25 + $0.50 = $6.75.
    cost = model_cost_usd(
        "claude-opus-4-8",
        0,
        0,
        cache_creation_tokens=1_000_000,
        cache_read_tokens=1_000_000,
    )
    assert cost == pytest.approx(6.75)


def test_zero_tokens_is_zero_cost() -> None:
    assert model_cost_usd("claude-haiku-4-5-20251001", 0, 0) == 0.0


def test_unknown_model_raises_keyerror() -> None:
    with pytest.raises(KeyError):
        model_cost_usd("gpt-4o", 1000, 1000)


def test_pricing_table_has_all_current_tiers() -> None:
    for model in (
        "claude-opus-4-8",
        "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001",
    ):
        entry = PRICING_USD_PER_MTOK[model]
        assert {"input", "output", "cache_creation", "cache_read"} <= entry.keys()
