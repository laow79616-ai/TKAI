"""Internal, non-outbound telemetry contracts."""

from ..contracts import Observation

OUTBOUND_TELEMETRY_ENABLED = False

__all__ = ("OUTBOUND_TELEMETRY_ENABLED", "Observation")
