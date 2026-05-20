"""Verifier helpers (library-mode, SA-003).

Pure-function checks that catch errors without spending tokens. Per the
v2 charter, this is the "eliminate API calls" lever: whenever a check
can be expressed deterministically against local data, prefer it over a
critic call.

Two conceptual flavors (the brief calls them "two flavors"):

- **Schema verifiers** — business rules beyond what Pydantic enforces.
  Examples: "if verdict is approved then revision_guidance must be
  empty", "probabilities sum to 1.0", "every claim has at least one
  invalidation_condition".
- **Evidence verifiers** — does each citation in the output resolve
  against the source data? This generalizes spectacular's
  `build_claim_lineage` pattern. Examples: "every signal cited in the
  brief exists in the processed signal data", "every doc reference in
  the lens output corresponds to a real header in the reference doc".

Both flavors share the same kernel loop and the same `VerifierIssue` /
`VerificationResult` types. The convenience wrappers `verify_schema` and
`verify_evidence` exist just to match the brief's two-flavor naming —
consumers who want maximum flexibility can compose closures and call
`verify()` directly.

Typical consumer:

    from spec_agents.agents.verifiers import (
        VerifierIssue, verify_schema, verify_evidence,
    )

    def all_claims_have_invalidation(brief: dict) -> list[VerifierIssue]:
        out = []
        for i, c in enumerate(brief.get("claims") or []):
            if not c.get("invalidation_conditions"):
                out.append(VerifierIssue(
                    code="claim.no_invalidation",
                    message="claim has no invalidation_conditions",
                    location=f"claims[{i}]",
                ))
        return out

    schema_result = verify_schema(brief, rules=[all_claims_have_invalidation])
    if not schema_result.passed:
        for issue in schema_result.issues:
            log.warning("verifier.fail", **asdict(issue))
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import partial
from typing import Any

import structlog

log = structlog.get_logger()


_SEVERITY_RANK: dict[str, int] = {
    "info": 0,
    "warning": 1,
    "error": 2,
    "critical": 3,
}


@dataclass(frozen=True)
class VerifierIssue:
    """One verifier complaint.

    ``code`` is a short stable identifier (good for filtering, metrics,
    test assertions). ``message`` is the human-readable explanation.
    ``location`` is a dotted-path / index pointer into the output where
    the issue lives (e.g. ``"claims[2].invalidation_conditions"``).
    ``severity`` defaults to ``"error"``; ``verify()`` and friends use
    severity to decide whether the overall verification passed.
    """

    code: str
    message: str
    location: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class VerificationResult:
    """Aggregate of one verify() call.

    ``passed`` is False iff any issue has severity at or above the
    configured fail threshold (default ``"error"``).
    """

    passed: bool
    issues: list[VerifierIssue]


# Generic verifier shape: no-arg callable returning a list of issues. The
# caller is responsible for binding whatever data each rule needs (via
# closures, partials, or the verify_schema / verify_evidence wrappers).
Verifier = Callable[[], list[VerifierIssue]]


def _at_or_above(severity: str, threshold: str) -> bool:
    """Severity comparison. Unknown severities rank highest (treated as
    failing) so callers can't accidentally hide a check by typo'ing the
    severity string."""
    return _SEVERITY_RANK.get(severity, 99) >= _SEVERITY_RANK.get(threshold, 99)


def verify(
    *,
    rules: Sequence[Verifier],
    fail_severity: str = "error",
) -> VerificationResult:
    """Run a sequence of no-arg verifier callables. Aggregate their issues.

    Each rule returns a list of issues. An empty list means the rule had
    no complaints. Exceptions from a rule are captured as a single
    ``verifier.crash`` issue (severity ``error``) so one broken rule
    doesn't silently swallow the whole verification.

    Args:
        rules: The verifiers to run. Compose with closures / partials to
            bind the data each rule needs.
        fail_severity: Issues at or above this severity cause
            ``passed=False``. Default ``"error"``; pass ``"warning"`` to
            fail strict. The rank order is ``info < warning < error <
            critical``; unknown strings rank highest (treated as fail).
    """
    issues: list[VerifierIssue] = []
    for rule in rules:
        try:
            issues.extend(rule())
        except Exception as exc:
            issues.append(
                VerifierIssue(
                    code="verifier.crash",
                    message=f"{getattr(rule, '__name__', repr(rule))} raised: {exc}",
                    severity="error",
                )
            )
            log.warning(
                "verifier.rule_crashed",
                rule=getattr(rule, "__name__", repr(rule)),
                error=str(exc),
            )

    passed = not any(_at_or_above(i.severity, fail_severity) for i in issues)
    return VerificationResult(passed=passed, issues=issues)


def verify_schema(
    output: dict[str, Any],
    *,
    rules: Sequence[Callable[[dict[str, Any]], list[VerifierIssue]]],
    fail_severity: str = "error",
) -> VerificationResult:
    """Convenience entry for schema-style rules: each rule takes the
    output dict and returns issues. The kernel ``verify()`` is called
    with closures that bind ``output`` to each rule.
    """
    return verify(
        rules=[partial(rule, output) for rule in rules],
        fail_severity=fail_severity,
    )


def verify_evidence(
    output: dict[str, Any],
    source: dict[str, Any],
    *,
    rules: Sequence[Callable[[dict[str, Any], dict[str, Any]], list[VerifierIssue]]],
    fail_severity: str = "error",
) -> VerificationResult:
    """Convenience entry for evidence-style rules: each rule takes
    ``(output, source)`` and returns issues for citations that don't
    resolve, mischaracterized values, etc. The kernel ``verify()`` is
    called with closures that bind both args to each rule.
    """
    return verify(
        rules=[partial(rule, output, source) for rule in rules],
        fail_severity=fail_severity,
    )
