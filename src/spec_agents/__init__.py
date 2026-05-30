"""spec_agents — reusable agent + adapter primitives.

Extracted from the spec_report (crypto research) project. Domain-agnostic
patterns that any "ingest data → run agents → produce report" application
can build on.

Submodules:
  agents               - Agent-side primitives: critic (SA-002), verifiers
                         (SA-003), plan-then-act (SA-004), parallel.map_agent
                         (Haiku-parallel item processing over a warmed cache)
  caching              - Token-wise prompt-cache helpers: cached_text_block +
                         warm_then_fan_out (avoid concurrent cache-miss storms)
  eval                 - Eval-harness runner (XR-010)
  ingestion.adapters   - Adapter ABC, scheduler primitives
  knowledge            - Lens + memory layer for LLM context
  logging              - Structured logging setup
  storage              - SQLAlchemy session/engine helpers
  messages             - Generic Pydantic message types
  testing              - Test fixtures (in-memory SQLite helper, XR-009)
  usage                - Single-source Anthropic pricing + model_cost_usd
"""

__version__ = "0.10.0"
