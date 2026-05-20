"""Smoke tests for spec_agents.agents.verifiers (SA-003)."""

from __future__ import annotations

from typing import Any

from spec_agents.agents.verifiers import (
    VerificationResult,
    VerifierIssue,
    verify,
    verify_evidence,
    verify_schema,
)


def test_verify_with_no_rules_passes() -> None:
    result = verify(rules=[])
    assert result.passed is True
    assert result.issues == []


def test_verify_with_passing_rule() -> None:
    def always_clean() -> list[VerifierIssue]:
        return []

    result = verify(rules=[always_clean])
    assert result.passed is True
    assert result.issues == []


def test_verify_with_failing_rule() -> None:
    def always_complains() -> list[VerifierIssue]:
        return [VerifierIssue(code="x.bad", message="something wrong")]

    result = verify(rules=[always_complains])
    assert result.passed is False
    assert len(result.issues) == 1
    assert result.issues[0].code == "x.bad"


def test_verify_aggregates_multiple_rules() -> None:
    def rule_a() -> list[VerifierIssue]:
        return [VerifierIssue(code="a.1", message="A1"), VerifierIssue(code="a.2", message="A2")]

    def rule_b() -> list[VerifierIssue]:
        return [VerifierIssue(code="b.1", message="B1")]

    result = verify(rules=[rule_a, rule_b])
    assert len(result.issues) == 3
    assert {i.code for i in result.issues} == {"a.1", "a.2", "b.1"}


def test_verify_captures_crashed_rule_as_issue() -> None:
    """A rule that raises shouldn't swallow the verification — emit a
    crash issue and keep going."""

    def crashy() -> list[VerifierIssue]:
        raise RuntimeError("boom")

    def clean() -> list[VerifierIssue]:
        return []

    result = verify(rules=[crashy, clean])
    assert result.passed is False
    assert len(result.issues) == 1
    assert result.issues[0].code == "verifier.crash"
    assert "boom" in result.issues[0].message
    assert "crashy" in result.issues[0].message


def test_verify_warning_doesnt_fail_at_default_threshold() -> None:
    def warner() -> list[VerifierIssue]:
        return [VerifierIssue(code="x.warn", message="heads up", severity="warning")]

    result = verify(rules=[warner])
    assert result.passed is True  # warnings under default fail_severity="error"
    assert len(result.issues) == 1


def test_verify_warning_fails_when_threshold_is_warning() -> None:
    def warner() -> list[VerifierIssue]:
        return [VerifierIssue(code="x.warn", message="heads up", severity="warning")]

    result = verify(rules=[warner], fail_severity="warning")
    assert result.passed is False


def test_verify_critical_fails_at_default_threshold() -> None:
    def emit_critical() -> list[VerifierIssue]:
        return [VerifierIssue(code="x.crit", message="bad", severity="critical")]

    result = verify(rules=[emit_critical])
    assert result.passed is False


def test_verify_unknown_severity_treated_as_failing() -> None:
    """Defensive: a typo'd severity shouldn't sneak past — rank as worst."""

    def typo() -> list[VerifierIssue]:
        return [VerifierIssue(code="x.typo", message="...", severity="eror")]

    result = verify(rules=[typo])
    assert result.passed is False


def test_verify_schema_passes_output_to_each_rule() -> None:
    captured: list[dict[str, Any]] = []

    def rule(output: dict[str, Any]) -> list[VerifierIssue]:
        captured.append(output)
        return []

    payload = {"verdict": "approved", "claims": [1, 2, 3]}
    verify_schema(payload, rules=[rule])
    assert captured == [payload]


def test_verify_schema_reports_business_rule_violation() -> None:
    def approved_means_no_guidance(output: dict[str, Any]) -> list[VerifierIssue]:
        if output.get("verdict") == "approved" and output.get("revision_guidance"):
            return [
                VerifierIssue(
                    code="schema.approved_with_guidance",
                    message="verdict is 'approved' but revision_guidance is non-empty",
                    location="revision_guidance",
                )
            ]
        return []

    bad = {"verdict": "approved", "revision_guidance": "fix the calibration"}
    good = {"verdict": "approved", "revision_guidance": ""}

    bad_result = verify_schema(bad, rules=[approved_means_no_guidance])
    assert bad_result.passed is False
    assert bad_result.issues[0].code == "schema.approved_with_guidance"
    assert bad_result.issues[0].location == "revision_guidance"

    good_result = verify_schema(good, rules=[approved_means_no_guidance])
    assert good_result.passed is True


def test_verify_evidence_passes_output_and_source_to_each_rule() -> None:
    seen: list[tuple[dict[str, Any], dict[str, Any]]] = []

    def rule(output: dict[str, Any], source: dict[str, Any]) -> list[VerifierIssue]:
        seen.append((output, source))
        return []

    payload = {"claims": []}
    src = {"signal_a": {"value": 1}}
    verify_evidence(payload, src, rules=[rule])
    assert seen == [(payload, src)]


def test_verify_evidence_flags_unresolved_citation() -> None:
    """Realistic shape: spectacular's signal-to-claim lineage idea, but
    generalized — caller writes a rule that checks each citation in
    output against source."""

    def citations_resolve(output: dict[str, Any], source: dict[str, Any]) -> list[VerifierIssue]:
        issues: list[VerifierIssue] = []
        for i, claim in enumerate(output.get("claims") or []):
            for cited in claim.get("cites") or []:
                if cited not in source:
                    issues.append(
                        VerifierIssue(
                            code="evidence.unresolved_citation",
                            message=f"claim cites '{cited}' but it's not in source",
                            location=f"claims[{i}].cites",
                        )
                    )
        return issues

    output = {
        "claims": [
            {"cites": ["signal_a", "signal_b"]},
            {"cites": ["signal_phantom"]},
        ]
    }
    source = {"signal_a": {}, "signal_b": {}}

    result = verify_evidence(output, source, rules=[citations_resolve])
    assert result.passed is False
    assert len(result.issues) == 1
    assert result.issues[0].code == "evidence.unresolved_citation"
    assert "signal_phantom" in result.issues[0].message


def test_result_passed_uses_severity_threshold_correctly() -> None:
    """Mixed-severity issues, default threshold: only errors fail."""

    def mixed() -> list[VerifierIssue]:
        return [
            VerifierIssue(code="a", message="info", severity="info"),
            VerifierIssue(code="b", message="warn", severity="warning"),
        ]

    result: VerificationResult = verify(rules=[mixed])
    assert result.passed is True  # no errors
    assert len(result.issues) == 2
