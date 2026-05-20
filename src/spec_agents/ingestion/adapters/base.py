"""Adapter base class. All data source adapters inherit from Adapter.

Contract:
  - fetch() returns a list of RawMetricIn dataclasses
  - Every adapter declares its cadence, staleness tolerance, and priority
  - The scheduler uses these to decide when and in what order to run adapters

This is a pure ABC + DTO module with zero domain dependencies. Use for any
"pull from external source → normalize → persist as time-series rows"
ingestion pattern.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import IntEnum


class AdapterPriority(IntEnum):
    CRITICAL = 1  # high-cadence signals — run first, alert on staleness
    HIGH = 2  # daily on-chain / behavioral
    NORMAL = 3  # daily price / volume
    LOW = 4  # weekly macro / context


@dataclass
class RawMetricIn:
    """Data transfer object from adapter to storage layer."""

    observed_at: datetime
    effective_at: datetime
    asset_id: str
    source: str
    source_version: str
    metric: str
    value: float | None = None
    value_text: str | None = None


class Adapter(ABC):
    """Base class for all data source adapters.

    Subclasses must implement fetch() and set class-level attributes:
        source: str — unique source identifier
        source_version: str — bumped when fetch logic changes
        expected_cadence: timedelta — how often this adapter should run
        staleness_threshold: timedelta — when to flag data as stale
        priority: AdapterPriority — scheduler ordering
    """

    source: str = ""
    source_version: str = "1.0.0"
    expected_cadence: timedelta = timedelta(hours=24)
    staleness_threshold: timedelta = timedelta(hours=26)
    priority: AdapterPriority = AdapterPriority.NORMAL

    def __init__(self, asset_id: str) -> None:
        if not self.source:
            raise TypeError(f"{type(self).__name__} must define class attribute 'source'")
        self.asset_id = asset_id

    @abstractmethod
    def fetch(self) -> list[RawMetricIn]:
        """Fetch current data for self.asset_id from the external source.

        Returns a list of RawMetricIn objects ready for storage.
        Raises on unrecoverable errors. Callers handle retry logic.
        """
        ...

    def __repr__(self) -> str:
        return f"{type(self).__name__}(asset_id={self.asset_id!r})"
