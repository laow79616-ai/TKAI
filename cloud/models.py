"""Immutable Cloud architecture models with no persistence or network effects."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType

CloudValue = str | int | float | bool | None


def snapshot(value: Mapping[str, CloudValue]) -> Mapping[str, CloudValue]:
    """Return a defensive, read-only mapping snapshot."""
    return MappingProxyType(dict(value))


class DeploymentStatus(str, Enum):
    """Declarative deployment state; no deployment action is performed."""

    DRAFT = "draft"
    READY = "ready"
    DEPLOYED = "deployed"
    FAILED = "failed"
    STOPPED = "stopped"


class ExecutionStatus(str, Enum):
    """Declarative cloud execution state."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProjectStatus(str, Enum):
    """Declarative project lifecycle state without a lifecycle service."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"


@dataclass(frozen=True, slots=True)
class Account:
    """Cloud account descriptor without authentication or billing behavior."""

    account_id: str
    name: str
    organization_id: str | None = None
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.account_id or not self.name:
            raise ValueError("Account id and name must not be empty.")
        object.__setattr__(self, "metadata", snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class Workspace:
    """Cloud workspace descriptor scoped to an explicit account."""

    workspace_id: str
    account_id: str
    name: str
    region: str | None = None
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.workspace_id or not self.account_id or not self.name:
            raise ValueError("Workspace id, account id, and name must not be empty.")
        object.__setattr__(self, "metadata", snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class Project:
    """Cloud project descriptor scoped to a caller-selected workspace."""

    project_id: str
    workspace_id: str
    name: str
    description: str = ""
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)
    slug: str | None = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    tags: frozenset[str] = field(default_factory=frozenset)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.project_id or not self.workspace_id or not self.name:
            raise ValueError("Project id, workspace id, and name must not be empty.")
        slug = (
            self.slug if self.slug is not None else self.name.lower().replace(" ", "-")
        )
        if not slug:
            raise ValueError("Project slug must not be empty.")
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise ValueError("Project timestamps must be timezone-aware.")
        object.__setattr__(self, "metadata", snapshot(self.metadata))
        object.__setattr__(self, "slug", slug)
        object.__setattr__(self, "tags", frozenset(self.tags))
        object.__setattr__(self, "created_at", self.created_at.astimezone(timezone.utc))
        object.__setattr__(self, "updated_at", self.updated_at.astimezone(timezone.utc))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe project snapshot without exposing mutable data."""
        return {
            "project_id": self.project_id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "status": self.status.value,
            "tags": sorted(self.tags),
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class Deployment:
    """Deployment plan descriptor; it does not provision any resource."""

    deployment_id: str
    project_id: str
    name: str
    status: DeploymentStatus = DeploymentStatus.DRAFT
    configuration: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.deployment_id or not self.project_id or not self.name:
            raise ValueError("Deployment id, project id, and name must not be empty.")
        object.__setattr__(self, "configuration", snapshot(self.configuration))


@dataclass(frozen=True, slots=True)
class Execution:
    """Execution descriptor reported by an explicit future gateway."""

    execution_id: str
    deployment_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.execution_id or not self.deployment_id:
            raise ValueError("Execution id and deployment id must not be empty.")
        object.__setattr__(self, "result", snapshot(self.result))


@dataclass(frozen=True, slots=True)
class StorageDescriptor:
    """Storage declaration without a filesystem, database, or object-store client."""

    storage_id: str
    workspace_id: str
    kind: str
    retention_days: int | None = None
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.storage_id or not self.workspace_id or not self.kind:
            raise ValueError("Storage id, workspace id, and kind must not be empty.")
        if self.retention_days is not None and self.retention_days < 0:
            raise ValueError("Storage retention must not be negative.")
        object.__setattr__(self, "metadata", snapshot(self.metadata))
