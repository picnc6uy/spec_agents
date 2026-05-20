"""Smoke test: spec_agents.testing.db helpers behave per their contract.

Tests the helper itself with a throwaway declarative model. Each test
gets a fresh engine and isolated state.
"""

from sqlalchemy import Column, Integer, String, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase

from spec_agents.testing.db import in_memory_engine, in_memory_session


class _Base(DeclarativeBase):
    pass


class _Widget(_Base):
    __tablename__ = "widgets"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


def test_in_memory_engine_is_sqlite_memory() -> None:
    engine = in_memory_engine()
    assert engine.url.drivername.startswith("sqlite")
    assert engine.url.database in (":memory:", None)
    engine.dispose()


def test_in_memory_session_round_trips_a_row() -> None:
    with in_memory_session(_Base.metadata) as session:
        session.add(_Widget(name="alpha"))
        session.commit()
        rows = session.query(_Widget).all()
        assert len(rows) == 1
        assert rows[0].name == "alpha"


def test_in_memory_session_isolates_between_calls() -> None:
    with in_memory_session(_Base.metadata) as s1:
        s1.add(_Widget(name="leak"))
        s1.commit()

    with in_memory_session(_Base.metadata) as s2:
        assert s2.query(_Widget).count() == 0


def test_schema_init_hooks_run_in_order_with_engine() -> None:
    calls: list[str] = []

    def hook_a(engine: Engine) -> None:
        calls.append(f"a:{engine.url.drivername}")

    def hook_b(engine: Engine) -> None:
        calls.append("b")

    with in_memory_session(_Base.metadata, schema_init=[hook_a, hook_b]):
        pass

    assert calls == ["a:sqlite", "b"]


def test_schema_init_can_execute_ddl() -> None:
    """The shape personal_os uses for FTS5: hook executes DDL the
    declarative MetaData can't express (virtual tables, triggers)."""

    def add_virtual_table(engine: Engine) -> None:
        with engine.begin() as conn:
            conn.execute(text("CREATE VIRTUAL TABLE widgets_fts USING fts5(name)"))

    with in_memory_session(_Base.metadata, schema_init=[add_virtual_table]) as session:
        result = session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='widgets_fts'")
        ).scalar_one()
        assert result == "widgets_fts"
