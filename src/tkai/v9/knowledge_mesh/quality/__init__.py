"""Explainable deterministic knowledge-quality evaluation."""

from collections.abc import Mapping

from tkai.v9.knowledge_mesh.models import QualityScore


def evaluate_quality(
    factors: Mapping[str, float], weights: Mapping[str, float]
) -> QualityScore:
    if not factors:
        return QualityScore(
            0.0,
            {},
            {},
            limitations=("no factors supplied",),
            explanation_summary="No quality evidence was supplied.",
        )
    if set(factors) != set(weights) or any(value < 0 for value in weights.values()):
        raise ValueError("factors and non-negative weights must have matching keys")
    total = sum(weights.values())
    if total <= 0 or any(not 0 <= value <= 1 for value in factors.values()):
        raise ValueError("quality inputs must be bounded")
    score = sum(factors[key] * weights[key] for key in factors) / total
    return QualityScore(
        score,
        factors,
        weights,
        explanation_summary="Weighted deterministic quality score.",
    )


__all__ = ("QualityScore", "evaluate_quality")
