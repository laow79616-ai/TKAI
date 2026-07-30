"""Confidence metadata validation."""

from __future__ import annotations

from tkai.v9.knowledge_mesh.contracts import ConfidenceRecord


def validate_confidence(value: float | None) -> float | None:
    if value is not None and not 0 <= value <= 1:
        raise ValueError("confidence must be between 0 and 1")
    return value


__all__ = ("ConfidenceRecord", "validate_confidence")
