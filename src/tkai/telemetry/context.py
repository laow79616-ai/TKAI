"""Correlation data independent of exporters and provider request state."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace


@dataclass(frozen=True, slots=True)
class CorrelationContext:
    request_id: str | None = None
    trace_id: str | None = None
    correlation_id: str | None = None
    provider: str | None = None
    operation: str | None = None

    def inherit(self, **changes: str | None) -> CorrelationContext:
        """Return a new context with explicit child overrides."""
        return replace(self, **changes)

    def copy(self) -> CorrelationContext:
        """Return an equivalent immutable context."""
        return replace(self)

    def to_dict(self) -> dict[str, str | None]:
        """Return stable JSON-ready correlation fields."""
        return asdict(self)
