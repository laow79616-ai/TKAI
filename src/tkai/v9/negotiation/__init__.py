"""Deterministic compatibility negotiation."""

from tkai.v9.compatibility import (
    NegotiationResult,
    negotiate_generations,
    negotiate_version,
)

__all__ = ("NegotiationResult", "negotiate_generations", "negotiate_version")
