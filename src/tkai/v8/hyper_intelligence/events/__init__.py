"""Metadata event names; this module contains no runtime event publisher."""

INTELLIGENCE_EVENTS = (
    "intelligence.metadata.aggregated",
    "intelligence.profile.registered",
    "intelligence.knowledge.registered",
    "intelligence.evidence.registered",
    "intelligence.signal.registered",
    "intelligence.recommendation.registered",
)

__all__ = ("INTELLIGENCE_EVENTS",)
