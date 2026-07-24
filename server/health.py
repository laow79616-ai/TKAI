"""Passive health report models; no network probes or background checks exist."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class HealthStatus(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class HealthCheck:
    name: str
    status: HealthStatus
    message: str = ""


@dataclass(frozen=True, slots=True)
class HealthReport:
    checks: tuple[HealthCheck, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "checks", tuple(sorted(self.checks, key=lambda item: item.name))
        )


@dataclass(frozen=True, slots=True)
class HealthSnapshot:
    report: HealthReport = field(default_factory=HealthReport)
