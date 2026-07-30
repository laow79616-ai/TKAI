"""Metadata event names; this module contains no runtime event publisher."""

KNOWLEDGE_EVENTS = (
    "knowledge.metadata.aggregated",
    "knowledge.profile.registered",
    "knowledge.knowledge.registered",
    "knowledge.evidence.registered",
    "knowledge.signal.registered",
    "knowledge.recommendation.registered",
)

__all__ = ("KNOWLEDGE_EVENTS",)
