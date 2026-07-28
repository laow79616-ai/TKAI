"""Domain contracts for the Enterprise TikTok AI Control Tower."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


CONTROL_TOWER_MODULES = (
    "runtime",
    "resources",
    "accounts",
    "browser_cluster",
    "devices",
    "proxies",
    "workflows",
    "scheduler",
    "automation",
    "execution",
    "publishing",
    "collection",
    "interaction",
    "risk",
    "analytics",
    "recovery",
)

DASHBOARD_SECTIONS = (
    "Overview",
    "Topology",
    "Runtime",
    "Resources",
    "Accounts",
    "Browsers",
    "Devices",
    "Proxies",
    "Publishing",
    "Collection",
    "Interaction",
    "Automation",
    "Execution",
    "Recovery",
    "Risk",
    "Analytics",
    "Alerts",
    "Activity",
)


@dataclass(frozen=True, slots=True)
class ControlTowerScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:control-tower:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class ModuleSnapshot:
    module: str
    tenant: str
    workspace: str
    health: HealthStatus
    status: str
    summary: dict[str, Any] = field(default_factory=dict)
    latency_seconds: float = 0.0
    observed_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["health"] = self.health.value
        return value


@dataclass(slots=True)
class ControlTowerAlert:
    id: str
    tenant: str
    workspace: str
    module: str
    severity: str
    message: str
    reference: str
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class ActivityEvent:
    tenant: str
    workspace: str
    actor: str
    action: str
    module: str
    detail: str
    timestamp: datetime = field(default_factory=utcnow)
