---
id: spec-agents-caching
title: spec_agents.caching — token-wise prompt-cache helpers (cached_text_block + warm_then_fan_out)
type: new-feature
lens: new-feature
created: 2026-05-29
status: drafted
budget:
  max_iterations: 40
  max_cost_usd: 4.00
  on_breach: abort-to-needs-rework
acceptance:
  - "NEW `src/spec_agents/caching.py` exports: `cached_text_block(text) -> dict` (text block with cache_control ephemeral), `warm_then_fan_out(tasks, run, *, max_workers=6, warm=True) -> list` (run task[0] serially to warm a shared cache, then fan out the rest concurrently, order preserved), and `is_cache_churning(cache_creation_tokens, cache_read_tokens, *, threshold=1.0) -> bool` (heuristic: creation dwarfs reads)."
  - "Library-mode: the module is pure / model-agnostic — no Anthropic client, no API calls, no I/O. `run` is caller-supplied. Matches usage.py's posture."
  - "warm_then_fan_out: empty tasks -> []; single task -> [run(t0)]; order preserved regardless of completion order; warm=True runs task[0] to completion BEFORE any fan-out task starts (deterministic test via threading.Event); warm=False fans all out; exceptions from run propagate."
  - "cached_text_block returns {'type':'text','text':text,'cache_control':{'type':'ephemeral'}} with a FRESH cache_control dict per call (no shared-mutable-default aliasing)."
  - "Tests in tests/test_caching.py: >=8 cases covering the above incl. the warm-before-fanout ordering guarantee and the churn heuristic. All pass."
  - "`spec_agents/__init__.py` submodule docstring lists the new `caching` module. Version bumped 0.8.0 -> 0.9.0 in pyproject.toml + __init__.py (kernel-freeze EXCEPTION — operator-granted 2026-05-29, mirrors the usage-cost-fn exception; recorded in this spec's Why)."
  - "Full suite green (existing + new); ruff check + ruff format clean; pyright strict-clean on the new module (it is in the include surface)."
files:
  touched:
    - src/spec_agents/caching.py            # NEW
    - src/spec_agents/__init__.py           # docstring submodule list + __version__ 0.9.0
    - pyproject.toml                         # version 0.8.0 -> 0.9.0
    - tests/test_caching.py                  # NEW
    - .agent/tasks/spec-agents-caching.md
    - .agent/verifications/spec-agents-caching.md
  must-not-touch:
    - src/spec_agents/usage.py               # consume conceptually; do not edit
    - src/spec_agents/agents/                # critic etc. consume later, not here
    - src/spec_agents/eval/
    - src/spec_agents/storage/
    - src/spec_agents/ingestion/
---

# spec-agents-caching: token-wise prompt-cache helpers

## Why
**Kernel-freeze exception, operator-granted 2026-05-29** (mirrors the `usage-cost-fn`
exception, review Open Q3). The freeze holds for everything else this cycle.

The audit-DAG A/B run on 2026-05-29 spent **$5.80 on the Opus pass alone** (vs a ~$0.37
estimate). Root cause measured from the usage ledger: `cache_creation` = 551K tokens / **$3.44**.
spectacular's audit reviewers fan out **6 calls concurrently** (`ThreadPoolExecutor`), each
carrying a ~130K-token cached corpus prefix. Because they fire simultaneously, none of the
cache writes has landed when the others start — so they all cache-MISS and each pays
`cache_creation` (1.25× input), which is *more expensive than not caching at all* (1.0×). The
cache optimization became a cost penalty.

This is a general hazard: **concurrent fan-out over a shared cached prefix = a cache-creation
storm.** It's currently one offender (the audit DAG), but it becomes pervasive the moment we add
Haiku parallel agents (the next initiative). The fix is a reusable kernel primitive so every
consumer — and the future parallel agents — inherits the correct pattern.

## What
NEW `src/spec_agents/caching.py`, pure + model-agnostic (library-mode):

1. `cached_text_block(text: str) -> dict[str, Any]` — build a content block with
   `cache_control: {"type": "ephemeral"}`. Doc: put the stable/large prefix in these blocks
   (ordered last among stable blocks, before the breakpoint); keep variable per-call content in
   the user turn (uncached). A fresh cache_control dict per call (no mutable-default aliasing).

2. `warm_then_fan_out(tasks, run, *, max_workers=6, warm=True) -> list` — the core primitive.
   When `warm=True` (tasks share a cached prefix): run `tasks[0]` serially to create the cache,
   then fan out `tasks[1:]` concurrently (they cache-read). When `warm=False` (tasks do NOT share
   a prefix — per-item prompts): fan out all immediately. Order preserved via an index->result
   map. `run` is caller-supplied and must be thread-safe w.r.t. what it closes over (the Anthropic
   SDK client is). Exceptions propagate.

3. `is_cache_churning(cache_creation_tokens, cache_read_tokens, *, threshold=1.0) -> bool` —
   heuristic the standard + monitoring use: True when creation:read ratio >= threshold (more
   re-writing than re-reading = the churn signature).

Also: `__init__.py` docstring submodule list + version 0.8.0 -> 0.9.0; pyproject version bump.

## Out of scope
- **Editing any consumer** (spectacular reviewers, critic) to USE these — that's the next sprint(s).
- Wrapping the Anthropic call / recording usage inside warm_then_fan_out — keep it model-agnostic;
  the caller's `run` owns the API call + usage recording (compose with `spec_agents.usage`).
- 1-hour extended cache TTL support — ephemeral (5-min) only for now; add a `ttl` param later if a
  consumer needs it (documented as a follow-up, not built).
- A stateful UsageTracker lift — separate, already noted in usage.py.
- Tagging/pushing v0.9.0 to GitHub or bumping consumer pins — operator-initiated release step.

## Notes
- New-feature lens: every new code path gets a test. The warm-before-fan-out guarantee is tested
  deterministically with a `threading.Event` (warm task sets it; fan-out tasks assert it's set on
  entry) — proving the property that yields "1 create + N-1 reads" in production, without needing
  real API calls.
- pyright strict: the new module is in the strict include. Type `run: Callable[[T], R]`,
  `tasks: Sequence[T]`; return `list[R]` built from an index map (no None-typed list).
- This primitive is dual-purpose: the caching fix AND the substrate for the planned Haiku
  parallel-agent processing (fan out many tasks, warm the shared prefix once).

## References
- A/B post-mortem 2026-05-29: usage ledger `spectacular/docs/audit_ab/usage_ledger.jsonl`
  (cache_creation 551K / $3.44 on the Opus pass).
- `spectacular/src/spectacular/agents/audit/reviewers.py:333` — the ThreadPoolExecutor fan-out.
- `src/spec_agents/usage.py` — the sibling pure-pricing module this mirrors in posture.
- v2 charter — library-mode discipline.
