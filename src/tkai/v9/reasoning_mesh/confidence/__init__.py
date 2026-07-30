"""Bounded confidence calibration without certainty claims."""

from __future__ import annotations

from collections.abc import Mapping

from tkai.v9.reasoning_mesh.contracts import Confidence, ReasoningScope, Reference


def calibrate(
    confidence_id: str,
    original: float,
    adjustments: Mapping[str, float],
    *,
    historical_accuracy_reference: Reference | None = None,
    limitations: tuple[str, ...] = (),
    scope: ReasoningScope | None = None,
) -> Confidence:
    required = (
        "evidence",
        "knowledge",
        "source",
        "freshness",
        "risk",
        "compatibility",
        "governance",
    )
    if set(adjustments) != set(required):
        raise ValueError("all named confidence adjustments are required")
    if not 0 <= original <= 1 or any(
        not 0 <= value <= 1 for value in adjustments.values()
    ):
        raise ValueError("confidence must be between 0 and 1")
    calibrated = sum((original, *adjustments.values())) / 8
    return Confidence(
        confidence_id,
        original,
        adjustments["evidence"],
        adjustments["knowledge"],
        adjustments["source"],
        adjustments["freshness"],
        adjustments["risk"],
        adjustments["compatibility"],
        adjustments["governance"],
        round(calibrated, 6),
        {"minimum": min(adjustments.values()), "maximum": max(adjustments.values())},
        historical_accuracy_reference,
        "Arithmetic calibration over bounded referenced factors; no certainty claimed.",
        limitations,
        scope=scope or ReasoningScope(),
    )


__all__ = ("calibrate",)
