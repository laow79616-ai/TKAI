"""TKAI V8 Hyper Reasoning Fabric public API."""

from tkai.v8.hyper_reasoning.contracts import (
    CompatibilityRecord,
    ConfidenceMetadata,
    EvidenceRecord,
    ExplanationSummary,
    ReasoningMetadata,
    ReasoningProfile,
    ReasoningReference,
    ReasoningScope,
    Recommendation,
)
from tkai.v8.hyper_reasoning.fabric import HyperReasoningFabric, ReasoningFabric

__all__ = (
    "CompatibilityRecord",
    "ConfidenceMetadata",
    "EvidenceRecord",
    "ExplanationSummary",
    "HyperReasoningFabric",
    "ReasoningFabric",
    "ReasoningMetadata",
    "ReasoningProfile",
    "ReasoningReference",
    "ReasoningScope",
    "Recommendation",
)
