"""In-memory SQLite helpers for fast, hermetic tests.

Domain-agnostic. Consumers pass their own `MetaData` (typically
`Base.metadata` from a declarative base). Optional `schema_init` hooks
run after `create_all` for things like FTS5 virtual tables that
SQLAlchemy's metadata can't express.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager

from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

SchemaInitHook = Callable[[Engine], None]


def in_memory_engine() -> Engine:
    """Return a fresh in-memory SQLite engine.

    Each call gets its own engine — `sqlite:///:memory:` is per-connection,
    so two engines do not share state. This is the right default for tests.
    """
    return create_engine("sqlite:///:memory:")


@contextmanager
def in_memory_session(
    metadata: MetaData,
    *,
    schema_init: Sequence[SchemaInitHook] = (),
) -> Iterator[Session]:
    """Yield a Session bound to a fresh in-memory database.

    Steps:
        1. Create a fresh in-memory engine.
        2. `metadata.create_all(engine)` — applies the consumer's schema.
        3. Run any `schema_init` hooks (e.g. FTS5 virtual table setup).
        4. Yield a `Session`. Caller uses it as a normal SQLAlchemy session.
        5. On exit, close the session and `drop_all` to release resources.

    The session is the only object the caller touches. Engine lifecycle
    is managed here so consumers never accidentally leak handles.

    Args:
        metadata: SQLAlchemy `MetaData` carrying the consumer's tables.
            Typically `Base.metadata`.
        schema_init: Optional callables run with the engine after
            `create_all`. Order is preserved. Use for things `MetaData`
            can't model (FTS5 virtual tables, triggers, views).

    Example:
        with in_memory_session(Base.metadata, schema_init=[init_fts5]) as s:
            s.add(MyModel(...))
            s.commit()
            assert s.query(MyModel).count() == 1
    """
    engine = in_memory_engine()
    metadata.create_all(engine)
    for hook in schema_init:
        hook(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        metadata.drop_all(engine)
        engine.dispose()
