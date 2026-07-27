"""Domain contracts for the enterprise TikTok Data Collection Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    CONFIGURED = "configured"
    VALIDATED = "validated"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class JobKind(str, Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    RECURRING = "recurring"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineStage(str, Enum):
    COLLECTION = "collection"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"
    STORAGE = "storage"
    ANALYTICS = "analytics"


@dataclass(frozen=True, slots=True)
class DataScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:data:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class CollectionSource:
    id: str
    tenant: str
    workspace: str
    configured_source: str
    account_reference: str
    collection_scope: dict[str, Any]
    validation: str = "pending"
    health: str = "unknown"

    def validate(self) -> None:
        if not all(
            (
                self.id,
                self.tenant,
                self.workspace,
                self.configured_source,
                self.account_reference,
            )
        ):
            raise ValueError("Configured source identity and scope are required.")
        forbidden = {"password", "secret", "token", "cookie", "credential"}
        if forbidden & {key.casefold() for key in self.collection_scope}:
            raise ValueError("Collection scope cannot contain secrets.")


@dataclass(slots=True)
class Dataset:
    id: str
    tenant: str
    workspace: str
    schema: str
    fields: list[str]
    encrypted_storage_reference: str
    tags: set[str] = field(default_factory=set)
    version: int = 1
    retention_days: int = 90
    record_count: int = 0
    archived: bool = False

    def validate(self) -> None:
        if not self.id or not self.schema or not self.fields:
            raise ValueError("Dataset ID, schema, and fields are required.")
        if len(set(self.fields)) != len(self.fields):
            raise ValueError("Dataset fields must be unique.")
        if self.version < 1 or not 1 <= self.retention_days <= 3650:
            raise ValueError("Dataset version or retention is invalid.")
        if not self.encrypted_storage_reference.startswith(("kms://", "vault://")):
            raise ValueError("Dataset must use an encrypted storage reference.")


@dataclass(slots=True)
class CollectionFilter:
    keywords: list[str] = field(default_factory=list)
    date_range: tuple[datetime | None, datetime | None] = (None, None)
    languages: set[str] = field(default_factory=set)
    regions: set[str] = field(default_factory=set)
    categories: set[str] = field(default_factory=set)
    deduplicate: bool = True
    validation_required: bool = True

    def validate(self) -> None:
        start, end = self.date_range
        if start and end and start > end:
            raise ValueError("Filter date range is invalid.")
        if any(not keyword.strip() for keyword in self.keywords):
            raise ValueError("Filter keywords cannot be empty.")


@dataclass(slots=True)
class CollectionProject:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    source_reference: str
    dataset_reference: str
    status: ProjectStatus = ProjectStatus.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all(
            (
                self.id,
                self.name,
                self.tenant,
                self.workspace,
                self.owner,
                self.source_reference,
                self.dataset_reference,
            )
        ):
            raise ValueError(
                "Project identity, ownership, source, and dataset required."
            )
        if self.version < 1:
            raise ValueError("Project version must be positive.")
        forbidden = {"password", "secret", "token", "cookie", "credential"}
        if forbidden & {key.casefold() for key in self.metadata}:
            raise ValueError("Project metadata cannot contain secrets.")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["created_at"] = self.created_at.isoformat()
        value["updated_at"] = self.updated_at.isoformat()
        return value


@dataclass(slots=True)
class CollectionTask:
    id: str
    project_reference: str
    tenant: str
    workspace: str
    kind: JobKind = JobKind.MANUAL
    priority: int = 50
    concurrency: int = 1
    maximum_retries: int = 3
    schedule: str = ""
    cancellable: bool = True
    status: JobStatus = JobStatus.QUEUED
    attempts: int = 0
    failure_reason: str = ""
    created_at: datetime = field(default_factory=utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None

    def validate(self) -> None:
        if not 0 <= self.priority <= 100:
            raise ValueError("Priority must be within [0, 100].")
        if not 1 <= self.concurrency <= 100 or not 0 <= self.maximum_retries <= 10:
            raise ValueError("Concurrency or retry policy is invalid.")
        if self.kind is not JobKind.MANUAL and not self.schedule:
            raise ValueError("Scheduled and recurring tasks require a schedule.")


@dataclass(slots=True)
class Pipeline:
    id: str
    tenant: str
    workspace: str
    project_reference: str
    stages: list[PipelineStage] = field(default_factory=lambda: list(PipelineStage))
    checkpoint: str = ""
    recovery_enabled: bool = True
    version: int = 1

    def validate(self) -> None:
        if not self.id or not self.project_reference or not self.stages:
            raise ValueError("Pipeline identity, project, and stages are required.")
        expected = [stage for stage in PipelineStage]
        if self.stages != expected:
            raise ValueError("Pipeline stages must follow the controlled stage order.")


@dataclass(slots=True)
class ExecutionRecord:
    job_reference: str
    project_reference: str
    tenant: str
    workspace: str
    status: JobStatus
    operator: str
    version: int
    timeline: list[dict[str, str]] = field(default_factory=list)
    audit_reference: str = ""
    started_at: datetime | None = None
    finished_at: datetime | None = None


@dataclass(slots=True)
class StorageOperation:
    id: str
    dataset_reference: str
    tenant: str
    workspace: str
    operation: str
    encrypted_reference: str
    occurred_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        allowed = {"import", "export", "archive", "restore"}
        if self.operation not in allowed:
            raise ValueError("Unsupported storage operation.")
        if not self.encrypted_reference.startswith(("kms://", "vault://")):
            raise ValueError("Storage operations require encrypted references.")
