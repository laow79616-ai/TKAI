"""Application Center value objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ApplicationStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    RUNNING = "running"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"


class SharingScope(str, Enum):
    PRIVATE = "private"
    TEAM = "team"
    ORGANIZATION = "organization"
    PUBLIC = "public"


class DeploymentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass(frozen=True)
class Application:
    id: str
    name: str
    description: str
    version: str
    owner: str
    category: str
    tags: tuple[str, ...] = ()
    status: ApplicationStatus = ApplicationStatus.DRAFT
    agent: str | None = None
    workflow: str | None = None
    plugins: tuple[str, ...] = ()
    knowledge: tuple[str, ...] = ()
    model: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    sharing: SharingScope = SharingScope.PRIVATE
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApplicationTemplate:
    id: str
    name: str
    category: str
    description: str
    defaults: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Deployment:
    id: str
    application_id: str
    version: str
    environment: str
    replicas: int
    quota: int
    status: DeploymentStatus
    created_by: str
    runs: int = 0
    failures: int = 0
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
