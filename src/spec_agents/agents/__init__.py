"""Agent-side primitives (library-mode).

Per the v2 charter, the kernel does not orchestrate. Submodules here expose
plain Python callables that agents (in apps, in Claude Code, anywhere) compose
into their own workflows.

Current primitives:
  - critic: forced-tool-use critic call. (SA-002)

Queued (per planning/SYSTEM.md):
  - verifiers: schema + evidence verifiers that catch errors without spending tokens (SA-003).
  - plan-then-act: two-call orchestration for structured decisions (SA-004).
"""
