"""Agent-side primitives (library-mode).

Per the v2 charter, the kernel does not orchestrate. Submodules here expose
plain Python callables that agents (in apps, in Claude Code, anywhere) compose
into their own workflows.

Current primitives:
  - critic: forced-tool-use critic call. (SA-002)
  - verifiers: schema + evidence verifiers that catch errors without
    spending tokens. (SA-003)
  - plan_then_act: two-call orchestration for structured decisions
    (SA-004). Composes two critic.critique calls — library-mode at its
    purest: kernel adds zero LLM-orchestration code beyond the
    composition.
  - parallel: map_agent — fan a per-item model call (Haiku by default) over
    many items with a warmed shared cache; returns results + aggregated
    cost/usage. For massive item processing. Composes spec_agents.caching
    (warm_then_fan_out) + spec_agents.usage.
"""
