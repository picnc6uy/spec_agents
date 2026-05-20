"""Smoke test: AgentMessage enforces its falsifiability invariant.

The validator on `invalidation_conditions` is a design decision encoded
in the public surface — every claim must be falsifiable. This test
guards that contract.
"""

import pytest
from pydantic import ValidationError

from spec_agents.messages import AgentMessage


def _valid_payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "agent_id": "test-agent",
        "agent_version": "0.0.1",
        "run_id": "run-1",
        "model": "claude-opus-4-7",
        "temperature": 0.0,
        "input_hash": "abc123",
        "reasoning_chain": ["step 1", "step 2"],
        "conclusion": "test conclusion",
        "direction": "neutral",
        "confidence": 0.5,
        "confidence_basis": ["basis 1"],
        "contradicting_evidence": [],
        "uncertainty_factors": ["factor 1"],
        "invalidation_conditions": ["if X happens, this is wrong"],
    }
    base.update(overrides)
    return base


def test_valid_agent_message_constructs() -> None:
    msg = AgentMessage(**_valid_payload())
    assert msg.confidence == 0.5
    assert msg.direction == "neutral"
    assert msg.invalidation_conditions == ["if X happens, this is wrong"]


def test_empty_invalidation_conditions_rejected() -> None:
    with pytest.raises(ValidationError, match="invalidation_conditions cannot be empty"):
        AgentMessage(**_valid_payload(invalidation_conditions=[]))


def test_confidence_outside_unit_interval_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentMessage(**_valid_payload(confidence=1.5))
