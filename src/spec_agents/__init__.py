"""spec_agents — reusable agent + adapter primitives.

Extracted from the spec_report (crypto research) project. Domain-agnostic
patterns that any "ingest data → run agents → produce report" application
can build on.

Submodules:
  ingestion.adapters   - Adapter ABC, scheduler primitives
  knowledge            - Lens + memory layer for LLM context
  logging              - Structured logging setup
  storage              - SQLAlchemy session/engine helpers
  messages             - Generic Pydantic message types
"""

__version__ = "0.1.0"
