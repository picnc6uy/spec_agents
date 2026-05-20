"""Database engine and session factory (domain-agnostic).

Usage:
    from spec_agents.storage import init_db, get_session
    from myapp.storage.models import Base

    init_db("sqlite:///./myapp.db", Base.metadata)

    with get_session() as session:
        session.add(row)
        session.commit()

The caller passes their SQLAlchemy `metadata` object — this module does
not import any domain models. Both spec_report (crypto) and personal_os
(or whatever) can share the same engine/session machinery.
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

if TYPE_CHECKING:
    from sqlalchemy import MetaData

_engine: object = None
_SessionFactory: object = None


def init_db(database_url: str, metadata: "MetaData | None" = None) -> None:
    """Initialize the engine and (optionally) create tables.

    Pass `metadata` to have the engine create all tables defined on that
    metadata object. Omit `metadata` if the caller manages schema some
    other way (Alembic migrations, separate process, etc.).
    """
    global _engine, _SessionFactory

    _engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    )

    if "sqlite" in database_url:

        @event.listens_for(_engine, "connect")  # type: ignore[misc]
        def set_sqlite_pragma(dbapi_conn: object, _: object) -> None:
            cursor = dbapi_conn.cursor()  # type: ignore[union-attr]
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    _SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False)
    if metadata is not None:
        metadata.create_all(_engine)  # type: ignore[arg-type]


@contextmanager
def get_session() -> Generator[Session, None, None]:
    if _SessionFactory is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    session: Session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
