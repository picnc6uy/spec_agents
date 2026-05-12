"""Generic agent message protocol — the canonical contract of the agent layer.

All agents speak this language. This module does not change without a version
bump and a corresponding migration of stored agent outputs.

Design decisions encoded here:
  - direction is a structured Literal, not free text (enables ensemble agreement)
  - confidence is float 0-1, not categorical (enables Bayesian weighting)
  - invalidation_conditions are required (enforces falsifiable claims)
  - input_hash covers content only, not metadata (enables reproducibility)

NOTE on direction naming: the Literal uses finance-domain terms
("bullish", "bearish", "neutral") because this module was extracted from a
crypto research project. Consumers in other domains can either reinterpret
("bullish" = positive signal, "bearish" = negative signal) or subclass with
their own Literal type.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Direction = Literal["bullish", "bearish", "neutral"]


class AgentMessage(BaseModel):
    """Single agent's output: a structured analytical message."""

    agent_id: str
    agent_version: str
    run_id: str
    model: str
    temperature: float
    input_hash: str          # SHA256 of input content — excludes timestamps/run metadata
    ensemble_run: int = 1    # which run in the ensemble (1-indexed)
    reasoning_chain: list[str]
    conclusion: str          # natural language narrative
    direction: Direction     # structured for ensemble agreement
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_basis: list[str]
    contradicting_evidence: list[str]
    uncertainty_factors: list[str]
    invalidation_conditions: list[str]

    @field_validator("invalidation_conditions")
    @classmethod
    def must_have_conditions(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError(
                "invalidation_conditions cannot be empty. "
                "Every claim must be falsifiable."
            )
        return v


class EnsembleResult(BaseModel):
    """Aggregated result across N runs of the same agent node."""

    agent_id: str
    runs: int
    agreement_rate: float = Field(ge=0.0, le=1.0)
    majority_direction: Direction
    majority_conclusion: str
    dissenting_conclusions: list[str]
    confidence_mean: float
    confidence_std: float
    inter_run_variance: float
    run_ids: list[str]


class EvidenceItem(BaseModel):
    """Structured evidence unit for Bayesian synthesis."""

    source_agent: str
    claim: str
    direction: Direction
    prior: float = Field(ge=0.0, le=1.0)
    likelihood_ratio: float
    source_weight: float = Field(ge=0.0, le=1.0)  # derived from track record
    posterior: float = Field(ge=0.0, le=1.0)
