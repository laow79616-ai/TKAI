"""Typed metadata contracts for the TKAI Business Platform product layer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Health(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class BusinessScope:
    tenant: str = "default"
    workspace: str = "default"
    actor: str = "api"


@dataclass(frozen=True, slots=True)
class MetadataRecord:
    id: str
    name: str
    module: str
    kind: str
    tenant: str = "default"
    workspace: str = "default"
    status: str = "active"
    health: Health = Health.UNKNOWN
    tags: tuple[str, ...] = ()
    group: str = ""
    owner: str = ""
    references: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["health"] = self.health.value
        result["updated_at"] = self.updated_at.isoformat()
        return result


@dataclass(frozen=True, slots=True)
class ModuleDefinition:
    id: str
    title: str
    resources: tuple[str, ...]
    capabilities: tuple[str, ...]
    advisory_only: bool = True
    execution_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
