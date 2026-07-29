"""Liveness, readiness, dependency, framework, and platform health."""

from ..contracts import HealthRecord, HealthStatus

HEALTH_KINDS = (
    "liveness",
    "readiness",
    "heartbeat",
    "dependency",
    "framework",
    "platform",
)

__all__ = ("HEALTH_KINDS", "HealthRecord", "HealthStatus")
