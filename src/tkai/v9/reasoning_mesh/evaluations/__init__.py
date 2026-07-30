"""Deterministic, bounded and explainable metadata evaluations."""

from __future__ import annotations

from collections.abc import Mapping

from tkai.v9.reasoning_mesh.contracts import Evaluation, ReasoningScope, Reference

EVALUATION_TYPES = (
    "context_completeness",
    "source_reliability",
    "evidence_completeness",
    "evidence_integrity",
    "evidence_freshness",
    "knowledge_relevance",
    "knowledge_integrity",
    "signal_quality",
    "observation_quality",
    "hypothesis_quality",
    "assumption_quality",
    "constraint_compliance",
    "alternative_coverage",
    "risk_calibration",
    "confidence_calibration",
    "compatibility_quality",
    "governance_compliance",
    "recommendation_quality",
    "overall_reasoning_quality",
)


def evaluate(
    evaluation_id: str,
    evaluation_type: str,
    factors: Mapping[str, float],
    weights: Mapping[str, float],
    *,
    supporting_references: tuple[Reference, ...] = (),
    limitations: tuple[str, ...] = (),
    scope: ReasoningScope | None = None,
) -> Evaluation:
    if evaluation_type not in EVALUATION_TYPES:
        raise ValueError("unsupported evaluation type")
    if not factors or set(factors) != set(weights):
        raise ValueError("factors and weights must be non-empty and aligned")
    if any(not 0 <= item <= 1 for item in (*factors.values(), *weights.values())):
        raise ValueError("evaluation factors and weights must be bounded")
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("evaluation weights must have a positive total")
    score = sum(factors[key] * weights[key] for key in factors) / total
    return Evaluation(
        evaluation_id,
        evaluation_type,
        round(score, 6),
        factors,
        weights,
        supporting_references,
        limitations,
        f"{evaluation_type} is a weighted metadata score supported by "
        f"{len(supporting_references)} reference(s); it is advisory, not causal.",
        scope=scope or ReasoningScope(),
    )


__all__ = ("EVALUATION_TYPES", "evaluate")
