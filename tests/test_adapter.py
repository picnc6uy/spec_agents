"""Smoke test: the Adapter ABC enforces its contract on subclasses.

The Adapter base class requires subclasses to set a `source` class attribute.
This test exercises the runtime check in `Adapter.__init__` that catches
subclasses that forget.
"""

from datetime import datetime, timedelta

import pytest

from spec_agents.ingestion.adapters.base import (
    Adapter,
    AdapterPriority,
    RawMetricIn,
)


class _ProperSubclass(Adapter):
    source = "test-source"
    source_version = "1.0.0"
    expected_cadence = timedelta(hours=24)
    staleness_threshold = timedelta(hours=26)
    priority = AdapterPriority.NORMAL

    def fetch(self) -> list[RawMetricIn]:
        return [
            RawMetricIn(
                observed_at=datetime(2026, 5, 20),
                effective_at=datetime(2026, 5, 20),
                asset_id=self.asset_id,
                source=self.source,
                source_version=self.source_version,
                metric="test",
                value=1.0,
            )
        ]


class _MissingSource(Adapter):
    def fetch(self) -> list[RawMetricIn]:
        return []


def test_proper_subclass_instantiates() -> None:
    adapter = _ProperSubclass(asset_id="BTC")
    assert adapter.asset_id == "BTC"
    assert adapter.source == "test-source"
    rows = adapter.fetch()
    assert len(rows) == 1
    assert rows[0].asset_id == "BTC"


def test_subclass_without_source_raises() -> None:
    with pytest.raises(TypeError, match="must define class attribute 'source'"):
        _MissingSource(asset_id="BTC")
