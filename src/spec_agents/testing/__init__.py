"""Shared test helpers for consumers of spec_agents.

Per XR-009: extracts the in-memory SQLite pattern that personal_os and
spectacular both copy-pasted in their conftest. Consumers depend on
schema (their own `Base.metadata`); this module stays domain-agnostic.

USAGE in a consumer's tests/conftest.py:

    import pytest
    from spec_agents.testing.db import in_memory_session
    from my_project.storage.models import Base

    @pytest.fixture
    def in_memory_db():
        with in_memory_session(Base.metadata) as session:
            yield session
"""

from spec_agents.testing.db import in_memory_engine, in_memory_session

__all__ = ["in_memory_engine", "in_memory_session"]
