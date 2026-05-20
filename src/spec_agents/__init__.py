"""spec_agents — reusable agent + adapter primitives.

Extracted from the spec_report (crypto research) project. Domain-agnostic
patterns that any "ingest data → run agents → produce report" application
can build on.

Submodules:
  agents               - Agent-side primitives: critic (SA-002), verifiers
                         (SA-003 queued), plan-then-act (SA-004 queued)
  eval                 - Eval-harness runner (XR-010)
  ingestion.adapters   - Adapter ABC, scheduler primitives
  knowledge            - Lens + memory layer for LLM context
  logging              - Structured logging setup
  storage              - SQLAlchemy session/engine helpers
  messages             - Generic Pydantic message types
  testing              - Test fixtures (in-memory SQLite helper, XR-009)
"""

__version__ = "0.4.0"
