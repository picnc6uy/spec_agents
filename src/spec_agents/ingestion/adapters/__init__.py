"""Adapter primitives: base class + priority enum + DTO."""
from spec_agents.ingestion.adapters.base import Adapter, AdapterPriority, RawMetricIn

__all__ = ["Adapter", "AdapterPriority", "RawMetricIn"]
