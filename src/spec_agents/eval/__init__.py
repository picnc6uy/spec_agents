"""Eval harness (XR-010, library-mode).

Iterates historical runs, replays each via a caller-supplied invoker,
scores each output via a caller-supplied scorer, returns the result set.
The kernel provides the loop and aggregation helpers; the caller owns
the domain (prompt assembly, lens loading, ground truth, score function).

Per the v2 charter: measurable feedback is the bottleneck for lens
authorship. Without an eval harness, lens claims are unfalsifiable —
prompt engineering rather than calibrated experiment.

XR-011 (Batch API) will add async / Batch-API-backed invokers on top of
this surface — the kernel here stays sync + sequential so the contract
is testable without network or batch infrastructure.
"""

from spec_agents.eval.batch import (
    BatchResult,
    build_invoker,
    fetch_results,
    get_batch_status,
    submit_batch,
    wait_for_batch,
)
from spec_agents.eval.runner import (
    EvalResult,
    EvalRun,
    Invoker,
    Scorer,
    aggregate_numeric,
    run_eval,
)

__all__ = [
    "BatchResult",
    "EvalResult",
    "EvalRun",
    "Invoker",
    "Scorer",
    "aggregate_numeric",
    "build_invoker",
    "fetch_results",
    "get_batch_status",
    "run_eval",
    "submit_batch",
    "wait_for_batch",
]
