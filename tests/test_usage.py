"""Smoke tests for spec_agents.usage (single-source pricing)."""

from __future__ import annotations

import pytest

from spec_agents.usage import (
    LONG_PROMPT_PRICING_USD_PER_MTOK,
    LONG_PROMPT_THRESHOLD_TOKENS,
    PRICING_USD_PER_MTOK,
    model_cost_usd,
)


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


def test_opus_5_input_output_and_cache_cost() -> None:
    # 2M input + 1M output on Opus 5 = $10 + $25 = $35.
    cost = model_cost_usd("claude-opus-5", 2_000_000, 1_000_000)
    assert cost == pytest.approx(35.0)
    # 1M cache_creation + 1M cache_read = $6.25 + $0.50 = $6.75.
    cache_cost = model_cost_usd(
        "claude-opus-5",
        0,
        0,
        cache_creation_tokens=1_000_000,
        cache_read_tokens=1_000_000,
    )
    assert cache_cost == pytest.approx(6.75)


def test_sonnet_5_input_output_and_cache_cost() -> None:
    # 2M input + 1M output on Sonnet 5 = $4 + $10 = $14.
    cost = model_cost_usd("claude-sonnet-5", 2_000_000, 1_000_000)
    assert cost == pytest.approx(14.0)
    # 1M cache_creation + 1M cache_read = $2.50 + $0.20 = $2.70.
    cache_cost = model_cost_usd(
        "claude-sonnet-5",
        0,
        0,
        cache_creation_tokens=1_000_000,
        cache_read_tokens=1_000_000,
    )
    assert cache_cost == pytest.approx(2.70)


def test_fable_5_1_input_output_and_cache_cost() -> None:
    # 2M input + 1M output on Fable 5.1 = $20 + $50 = $70.
    cost = model_cost_usd("claude-fable-5-1", 2_000_000, 1_000_000)
    assert cost == pytest.approx(70.0)
    # 1M cache_creation + 1M cache_read = $12.50 + $0.25 = $12.75.
    cache_cost = model_cost_usd(
        "claude-fable-5-1",
        0,
        0,
        cache_creation_tokens=1_000_000,
        cache_read_tokens=1_000_000,
    )
    assert cache_cost == pytest.approx(12.75)


def test_fable_5_1_cache_read_is_flat_not_point_one_x_input() -> None:
    # Fable's cache_read is a FLAT $0.25/MTok, NOT 0.1x its $10 input price
    # (0.1x would be $1.00). 1M cache_read tokens -> $0.25, explicitly not $1.00.
    cost = model_cost_usd("claude-fable-5-1", 0, 0, cache_read_tokens=1_000_000)
    assert cost == pytest.approx(0.25)
    assert cost != pytest.approx(1.00)


def test_sonnet_5_is_cheaper_than_sonnet_4_6() -> None:
    kwargs = dict(
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        cache_creation_tokens=1_000_000,
        cache_read_tokens=1_000_000,
    )
    sonnet_5_cost = model_cost_usd("claude-sonnet-5", **kwargs)
    sonnet_4_6_cost = model_cost_usd("claude-sonnet-4-6", **kwargs)
    assert sonnet_5_cost < sonnet_4_6_cost


def test_pricing_table_has_all_current_tiers() -> None:
    for model in (
        "claude-opus-4-8",
        "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001",
    ):
        entry = PRICING_USD_PER_MTOK[model]
        assert {"input", "output", "cache_creation", "cache_read"} <= entry.keys()


# ── 5.5 models (sa-prices-55-1) ──────────────────────────────────────────

_MIXED = dict(
    input_tokens=300_000,
    output_tokens=70_000,
    cache_creation_tokens=40_000,
    cache_read_tokens=500_000,
)


def test_opus_5_5_mixed_call_by_hand() -> None:
    expected = (300_000 * 4.0 + 70_000 * 20.0 + 40_000 * 5.0 + 500_000 * 0.20) / 1_000_000
    assert abs(model_cost_usd("claude-opus-5-5", **_MIXED) - expected) < 1e-12


def test_sonnet_5_5_mixed_call_by_hand() -> None:
    expected = (300_000 * 2.0 + 70_000 * 10.0 + 40_000 * 2.50 + 500_000 * 0.10) / 1_000_000
    assert abs(model_cost_usd("claude-sonnet-5-5", **_MIXED) - expected) < 1e-12


def test_haiku_5_5_mixed_call_by_hand() -> None:
    # prompt 30k + 4k + 50k = 84k <= 100k: base rates.
    kw = dict(
        input_tokens=30_000,
        output_tokens=7_000,
        cache_creation_tokens=4_000,
        cache_read_tokens=50_000,
    )
    expected = (30_000 * 0.10 + 7_000 * 0.50 + 4_000 * 0.125 + 50_000 * 0.01) / 1_000_000
    assert abs(model_cost_usd("claude-haiku-5-5", **kw) - expected) < 1e-12


def test_5_5_cache_read_is_flat_not_point_one_x_input() -> None:
    opus = PRICING_USD_PER_MTOK["claude-opus-5-5"]
    sonnet = PRICING_USD_PER_MTOK["claude-sonnet-5-5"]
    assert opus["cache_read"] == 0.20 and opus["cache_read"] != 0.1 * opus["input"]
    assert sonnet["cache_read"] == 0.10 and sonnet["cache_read"] != 0.1 * sonnet["input"]
    assert model_cost_usd("claude-opus-5-5", 0, 0, cache_read_tokens=1_000_000) == pytest.approx(
        0.20
    )
    assert model_cost_usd("claude-sonnet-5-5", 0, 0, cache_read_tokens=1_000_000) == pytest.approx(
        0.10
    )


def test_haiku_5_5_threshold_boundary() -> None:
    base = model_cost_usd("claude-haiku-5-5", 100_000, 0)
    assert abs(base - 100_000 * 0.10 / 1_000_000) < 1e-12
    long = model_cost_usd("claude-haiku-5-5", 100_001, 0)
    assert abs(long - 100_001 * 0.50 / 1_000_000) < 1e-12


def test_haiku_5_5_long_prompt_all_token_kinds_at_long_rates() -> None:
    cost = model_cost_usd(
        "claude-haiku-5-5", 1_000, 2_000, cache_creation_tokens=3_000, cache_read_tokens=100_000
    )
    expected = (1_000 * 0.50 + 2_000 * 2.50 + 3_000 * 0.625 + 100_000 * 0.05) / 1_000_000
    assert abs(cost - expected) < 1e-12


def test_haiku_5_5_cache_reads_count_toward_threshold() -> None:
    cost = model_cost_usd("claude-haiku-5-5", 10, 0, cache_read_tokens=100_000)
    assert abs(cost - (10 * 0.50 + 100_000 * 0.05) / 1_000_000) < 1e-12


def test_haiku_5_5_output_does_not_count_toward_threshold() -> None:
    cost = model_cost_usd("claude-haiku-5-5", 50_000, 500_000)
    assert abs(cost - (50_000 * 0.10 + 500_000 * 0.50) / 1_000_000) < 1e-12


@pytest.mark.parametrize("model", ["claude-opus-5-5", "claude-sonnet-5-5"])
def test_5_5_big_models_have_no_threshold(model: str) -> None:
    small = model_cost_usd(model, 9_000, 0)
    big = model_cost_usd(model, 900_000, 0)
    assert big == pytest.approx(small * 100)


def test_pre_existing_rows_unchanged() -> None:
    expected = {
        "claude-opus-4-8": (5.0, 25.0, 6.25, 0.50),
        "claude-opus-4-7": (5.0, 25.0, 6.25, 0.50),
        "claude-sonnet-4-6": (3.0, 15.0, 3.75, 0.30),
        "claude-haiku-4-5-20251001": (1.0, 5.0, 1.25, 0.10),
        "claude-opus-5": (5.0, 25.0, 6.25, 0.50),
        "claude-sonnet-5": (2.0, 10.0, 2.50, 0.20),
        "claude-fable-5-1": (10.0, 50.0, 12.50, 0.25),
    }
    for model, (i, o, cc, cr) in expected.items():
        assert PRICING_USD_PER_MTOK[model] == {
            "input": i,
            "output": o,
            "cache_creation": cc,
            "cache_read": cr,
        }


def test_long_prompt_table_covers_only_haiku_5_5() -> None:
    assert set(LONG_PROMPT_PRICING_USD_PER_MTOK) == {"claude-haiku-5-5"}


@pytest.mark.parametrize(
    "model", ["gpt-4o", "claude-haiku-5-5-20260101", "claude-opus-5-5-20260101"]
)
def test_unknown_or_dated_5_5_id_raises_keyerror(model: str) -> None:
    with pytest.raises(KeyError):
        model_cost_usd(model, 1000, 1000)


def test_haiku_5_5_cache_creation_counts_toward_threshold() -> None:
    cost = model_cost_usd("claude-haiku-5-5", 10, 0, cache_creation_tokens=100_000)
    assert abs(cost - (10 * 0.50 + 100_000 * 0.625) / 1_000_000) < 1e-12


def test_new_rows_and_long_rows_have_all_four_keys() -> None:
    keys = {"input", "output", "cache_creation", "cache_read"}
    for model in ("claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"):
        assert PRICING_USD_PER_MTOK[model].keys() == keys
    for row in LONG_PROMPT_PRICING_USD_PER_MTOK.values():
        assert row.keys() == keys


def test_threshold_and_long_tables_have_same_models() -> None:
    assert LONG_PROMPT_THRESHOLD_TOKENS.keys() == LONG_PROMPT_PRICING_USD_PER_MTOK.keys()
    assert LONG_PROMPT_THRESHOLD_TOKENS.keys() <= PRICING_USD_PER_MTOK.keys()
