"""Smoke test: the public surface imports without error.

If a consumer's CI runs `python -c "import spec_agents"` and gets a stack
trace, the library is broken regardless of what its tests say. This file
guards the import contract documented in CLAUDE.md.
"""


def test_top_level_import() -> None:
    import spec_agents

    assert spec_agents.__version__


def test_public_surface_imports() -> None:
    from spec_agents.ingestion.adapters.base import Adapter, AdapterPriority, RawMetricIn
    from spec_agents.knowledge.lenses import Lens, LensLoader, LensSection
    from spec_agents.messages import AgentMessage, EnsembleResult, EvidenceItem

    assert Adapter.__name__ == "Adapter"
    assert AdapterPriority.NORMAL.value == 3
    assert RawMetricIn.__name__ == "RawMetricIn"
    assert LensLoader.__name__ == "LensLoader"
    assert Lens.__name__ == "Lens"
    assert LensSection.__name__ == "LensSection"
    assert AgentMessage.__name__ == "AgentMessage"
    assert EnsembleResult.__name__ == "EnsembleResult"
    assert EvidenceItem.__name__ == "EvidenceItem"
