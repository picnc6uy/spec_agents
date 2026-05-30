"""Parallel agent map — fan a per-item model call over many items, cache-correctly.

Library-mode (agents band, like :mod:`spec_agents.agents.critic`): a callable agents
compose, not a framework. The kernel does not orchestrate your workflow — it gives you
one cache-correct fan-out primitive.

For **massive item processing** (the Haiku workhorse case): put the large, stable
instruction/context in a cached system block (written once), give each item its specific
user prompt (the "agent task specificity"), and fan the calls out *after* the shared cache
is warm. This is exactly the shape that, done naively (all calls cold + concurrent),
triggers the cache-creation storm that :mod:`spec_agents.caching` exists to prevent — so
``map_agent`` builds on :func:`spec_agents.caching.warm_then_fan_out` to get it right by
construction, and rolls up per-call usage so a big run reports its true cost (and flags
churn if the cache isn't being reused).
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from spec_agents.caching import cached_text_block, is_cache_churning, warm_then_fan_out
from spec_agents.usage import model_cost_usd

__all__ = [
    "DEFAULT_PARALLEL_MODEL",
    "MapResult",
    "MapUsage",
    "map_agent",
]

T = TypeVar("T")
R = TypeVar("R")

#: Default model for parallel item processing — Haiku is the cheap, fast workhorse.
DEFAULT_PARALLEL_MODEL = "claude-haiku-4-5-20251001"


@dataclass(frozen=True)
class MapUsage:
    """Aggregated token usage + cost across a :func:`map_agent` fan-out."""

    calls: int
    input_tokens: int
    output_tokens: int
    cache_creation_tokens: int
    cache_read_tokens: int
    cost_usd: float
    #: True when the prefix was re-written more than re-read — caching is not paying off
    #: (e.g. the prefix differs per item, or warming was disabled). See is_cache_churning.
    churning: bool


@dataclass(frozen=True)
class MapResult(Generic[R]):
    """Results (in item order) plus the aggregated usage for a :func:`map_agent` run."""

    results: list[R]
    usage: MapUsage


def map_agent(
    *,
    client: Any,
    items: Sequence[T],
    shared_system_text: str,
    build_user_content: Callable[[T], Any],
    parse: Callable[[Any], R],
    model: str = DEFAULT_PARALLEL_MODEL,
    max_tokens: int = 2048,
    tools: list[Any] | None = None,
    tool_choice: dict[str, Any] | None = None,
    max_workers: int = 6,
    warm: bool = True,
) -> MapResult[R]:
    """Run one model call per item, fanned out over a warmed shared cache.

    The ``shared_system_text`` (large, stable: instructions + context) goes in a cached
    system block, written once. Each item's variable content comes from
    ``build_user_content(item)`` and lives in the user turn (uncached). With ``warm=True``
    the first item runs serially to create the cache, then the rest fan out and cache-read
    it — avoiding the concurrent cache-creation storm. Each response is turned into a result
    by ``parse(response)``.

    Args:
        client: an Anthropic client (or any object with ``messages.create(**kwargs)``).
        items: the work items, in the order results should be returned.
        shared_system_text: the stable, cacheable prefix shared by every item.
        build_user_content: ``item -> user content`` (str or content-block list).
        parse: ``response -> result``. Owns any tool-use extraction / validation.
        model: defaults to Haiku (:data:`DEFAULT_PARALLEL_MODEL`).
        max_tokens: per-call response budget.
        tools / tool_choice: forwarded to ``messages.create`` only when provided.
        max_workers: fan-out thread-pool cap.
        warm: warm the shared cache with ``items[0]`` before fanning out the rest. Set
            False only when items do NOT share the cached prefix.

    Returns:
        :class:`MapResult` — ``results`` in item order + a :class:`MapUsage` rollup
        (totals, ``cost_usd`` via :func:`spec_agents.usage.model_cost_usd`, and a
        ``churning`` flag via :func:`spec_agents.caching.is_cache_churning`).

    Raises:
        Propagates the first exception observed from ``messages.create`` / ``parse``.
    """
    system = [cached_text_block(shared_system_text)]
    records: list[tuple[int, int, int, int]] = []
    lock = threading.Lock()

    def _run(item: T) -> R:
        create_kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": build_user_content(item)}],
        }
        if tools is not None:
            create_kwargs["tools"] = tools
        if tool_choice is not None:
            create_kwargs["tool_choice"] = tool_choice

        response = client.messages.create(**create_kwargs)

        usage: Any = getattr(response, "usage", None)
        record = (
            int(getattr(usage, "input_tokens", 0) or 0),
            int(getattr(usage, "output_tokens", 0) or 0),
            int(getattr(usage, "cache_creation_input_tokens", 0) or 0),
            int(getattr(usage, "cache_read_input_tokens", 0) or 0),
        )
        with lock:
            records.append(record)
        return parse(response)

    results = warm_then_fan_out(items, _run, max_workers=max_workers, warm=warm)

    input_tokens = sum(r[0] for r in records)
    output_tokens = sum(r[1] for r in records)
    cache_creation = sum(r[2] for r in records)
    cache_read = sum(r[3] for r in records)
    cost = model_cost_usd(
        model,
        input_tokens,
        output_tokens,
        cache_creation_tokens=cache_creation,
        cache_read_tokens=cache_read,
    )
    usage_totals = MapUsage(
        calls=len(records),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_creation_tokens=cache_creation,
        cache_read_tokens=cache_read,
        cost_usd=cost,
        churning=is_cache_churning(cache_creation, cache_read),
    )
    return MapResult(results=results, usage=usage_totals)
