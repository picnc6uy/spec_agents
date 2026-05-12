# spec_agents

Reusable agent + adapter primitives extracted from `spectacular/spec_report`.

Domain-agnostic patterns any "ingest data → run agents → produce report" app
can build on:

- **Adapter ABC** — base class for data source adapters
- **Knowledge layer** — lenses (curated context) + memory (agent self-knowledge)
- **Database helpers** — SQLAlchemy session/engine setup
- **Logging** — structured logging via structlog
- **Messages** — generic Pydantic message types for agent communication

## Installing

```
pip install -e /path/to/spec_agents
```

## Provenance

Extracted 2026-05-12 from `c:\Users\ghendrick\spectacular\` after the
spec_report architecture stabilized. Both packages import from this one going
forward.
