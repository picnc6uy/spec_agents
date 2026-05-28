"""Lens-based knowledge layer for LLM context injection.

A "lens" is a named, focused extract from one or more reference docs. The
LensLoader class takes a docs root + a dict of lens definitions and exposes
load_lens() / load_lenses() methods that produce prompt-ready text.

NOTE: the `memory.py` (performance memory: recent critique verdicts + Brier
score trends) is intentionally NOT extracted into spec_agents because it
couples to domain-specific DB models. Each consumer writes its own memory
module over its own Brief-equivalent models.
"""

from spec_agents.knowledge.lenses import (
    Lens,
    LensLoader,
    LensSection,
    ValidationIssue,
)

__all__ = ["Lens", "LensLoader", "LensSection", "ValidationIssue"]
