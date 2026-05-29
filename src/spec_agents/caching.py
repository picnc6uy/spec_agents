"""Prompt-caching helpers — token-wise reuse of large, stable prefixes.

Library-mode (per the v2 charter): pure construction helpers plus one
orchestration primitive. This module owns no Anthropic client, makes no API
calls, and holds no state. Callers supply the work function; compose with
``spec_agents.usage`` to price the result.

Why this exists
---------------
Anthropic prompt caching only saves money under *serialized reuse*. A cached
prefix is written once (``cache_creation`` ≈ 1.25× input price) and then
re-read cheaply (``cache_read`` ≈ 0.1× input price) by later calls *within the
cache TTL*. But if N calls that share the prefix fire **concurrently**, they
all cache-miss before any write lands — each pays ``cache_creation`` (1.25×),
which is *more expensive than not caching at all* (1.0× plain input).

Measured 2026-05-29: a 6-way concurrent audit fan-out spent $3.44 on
``cache_creation`` re-writing the same ~130K-token corpus ~5×, turning a cost
optimization into a cost penalty.

The rule this module encodes
----------------------------
- Put stable/large content in a cached block (:func:`cached_text_block`);
  keep per-call variable content *after* the cache breakpoint (the user turn),
  so the cache key is shared. Any byte change before the breakpoint invalidates
  the cache.
- For concurrent fan-out over a shared prefix, **warm the cache with one call
  first, let it land, then fan out the rest** (:func:`warm_then_fan_out`).
- If you can't warm, don't cache — plain input (1.0×) beats concurrent
  ``cache_creation`` (1.25×).
- Measure: :func:`is_cache_churning` flags the creation-dwarfs-reads signature.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, TypeVar

__all__ = [
    "cached_text_block",
    "is_cache_churning",
    "warm_then_fan_out",
]

T = TypeVar("T")
R = TypeVar("R")


def cached_text_block(text: str) -> dict[str, Any]:
    """Build a text content block marked for Anthropic prompt caching.

    Use for the stable, large prefix (corpus, lenses, fixed instructions) that
    does not change across a set of calls. Order such blocks so the cached one
    is the LAST stable block before the cache breakpoint, and keep per-call
    variable content (the role, the specific question) in the user turn, which
    is not cached. Anthropic's cache key is the block prefix, so any byte change
    before the breakpoint invalidates the cache.

    Returns a fresh dict each call (including a fresh ``cache_control`` dict) so
    callers can mutate the result without aliasing a shared default.
    """
    return {
        "type": "text",
        "text": text,
        "cache_control": {"type": "ephemeral"},
    }


def warm_then_fan_out(
    tasks: Sequence[T],
    run: Callable[[T], R],
    *,
    max_workers: int = 6,
    warm: bool = True,
) -> list[R]:
    """Run ``run(task)`` for every task, preserving input order in the result.

    When the tasks share a cached prompt prefix, keep ``warm=True`` (default):
    the first task runs serially to create the cache entry, then the remaining
    tasks fan out concurrently and cache-READ it. This avoids the
    concurrent-cache-miss storm where every parallel call pays ``cache_creation``
    (1.25× input) instead of one create + (N-1) reads (0.1× input).

    Set ``warm=False`` to fan out all tasks immediately. That is the right
    choice when the tasks do NOT share a cached prefix (e.g. per-item prompts
    with no common cache): there is no warm-up benefit, so the serial first call
    would only add latency.

    Args:
        tasks: the work items, in the order results should be returned.
        run: ``task -> result``. Must be thread-safe with respect to anything it
            closes over. The Anthropic SDK client is safe for concurrent
            ``messages.create``.
        max_workers: cap on the fan-out thread pool.
        warm: warm the shared cache with ``tasks[0]`` before fanning out the rest.

    Returns:
        ``[run(tasks[0]), run(tasks[1]), ...]`` in input order, regardless of
        completion order.

    Raises:
        Propagates the first exception observed from ``run``.
    """
    n = len(tasks)
    if n == 0:
        return []

    out: dict[int, R] = {}
    if warm:
        out[0] = run(tasks[0])
        pending = list(range(1, n))
    else:
        pending = list(range(n))

    if pending:
        workers = max(1, min(max_workers, len(pending)))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(run, tasks[i]): i for i in pending}
            for future in as_completed(futures):
                out[futures[future]] = future.result()

    return [out[i] for i in range(n)]


def is_cache_churning(
    cache_creation_tokens: int,
    cache_read_tokens: int,
    *,
    threshold: float = 1.0,
) -> bool:
    """Heuristic: is the prompt cache being re-written more than re-read?

    A healthy cached fan-out writes the prefix once and reads it many times, so
    ``cache_read`` should dwarf ``cache_creation``. The inverse — creation near
    or above reads — is the signature of a concurrent-fan-out miss storm or TTL
    expiry between calls.

    Returns True when ``cache_creation_tokens / cache_read_tokens >= threshold``.
    With no creation, never churning. With creation but zero reads, always
    churning (the cache is being written and never reused).
    """
    if cache_creation_tokens <= 0:
        return False
    if cache_read_tokens <= 0:
        return True
    return (cache_creation_tokens / cache_read_tokens) >= threshold
