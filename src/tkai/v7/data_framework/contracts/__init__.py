"""Immutable contracts for the V7 local data metadata plane."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from types import MappingProxyType
from typing import Any

MAX_PAGE_SIZE = 100
MAX_RESULTS = 1000
MAX_SORT_FIELDS = 5
MAX_TIME_RANGE_DAYS = 366
SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$"
)
SAFE_REFERENCE_SCHEMES = (
    "ref://",
    "secret://",
    "payload://",
    "audit://",
    "snapshot://",
)
SECRET_NAMES = frozenset(
    {
        "api_key",
        "authorization",
        "cookie",
        "credential",
        "password",
        "proxy_credentials",
        "secret",
        "session",
        "token",
    }
)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def frozen_map(value: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


def required(value: str, name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} is required")


def validate_version(value: str) -> None:
    if not SEMVER.fullmatch(value):
        raise ValueError("version must use semantic versioning")


def validate_safe_metadata(value: Mapping[str, Any]) -> None:
    forbidden = SECRET_NAMES.intersection(key.lower() for key in value)
    if forbidden:
        raise ValueError(f"sensitive metadata is prohibited: {sorted(forbidden)}")


class Lifecycle(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    VALIDATED = "validated"
    AVAILABLE = "available"
    READ_ONLY = "read-only"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ValidationStatus(str, Enum):
    UNKNOWN = "unknown"
    VALID = "valid"
    INVALID = "invalid"
    REQUIRES_REVIEW = "requires-review"


class IntegrityStatus(str, Enum):
    UNKNOWN = "unknown"
    VALID = "valid"
    INVALID = "invalid"


class StorageKind(str, Enum):
    MEMORY = "memory"
    LOCAL_FILE = "local-file"
    SQLITE_METADATA = "sqlite-metadata"
    REPOSITORY = "repository"
    V6_DATABASE = "v6-database"
    SNAPSHOT = "snapshot"
    TEST = "test"
    MOCK = "mock"


class FilterOperator(str, Enum):
    EQUAL = "equal"
    NOT_EQUAL = "not-equal"
    IN = "in"
    NOT_IN = "not-in"
    RANGE = "range"
    PREFIX = "prefix"
    CONTAINS = "contains"
    DATE_RANGE = "date-range"


class SortDirection(str, Enum):
    ASCENDING = "ascending"
    DESCENDING = "descending"


@dataclass(frozen=True, slots=True)
class Scope:
    tenant_id: str
    workspace_id: str
    namespace: str = "data"

    def __post_init__(self) -> None:
        required(self.tenant_id, "tenant_id")
        required(self.workspace_id, "workspace_id")
        required(self.namespace, "namespace")


@dataclass(frozen=True, slots=True)
class Health:
    status: str = "unknown"
    checks: Mapping[str, str] = field(default_factory=frozen_map)
    observed_at: datetime = field(default_factory=now_utc)

    def __post_init__(self) -> None:
        object.__setattr__(self, "checks", frozen_map(self.checks))


@dataclass(frozen=True, slots=True)
class SchemaField:
    name: str
    type_name: str
    required: bool = False
    allowed_values: tuple[Any, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    format: str | None = None
    secret: bool = False
    indexed: bool = False
    immutable: bool = False
    deprecated: bool = False
    safe_default: Any = None

    def __post_init__(self) -> None:
        required(self.name, "field name")
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("minimum cannot exceed maximum")


@dataclass(frozen=True, slots=True)
class DataSchema:
    schema_id: str
    scope: Scope
    version: str
    fields: tuple[SchemaField, ...]
    compatibility: Mapping[str, str] = field(default_factory=frozen_map)

    def __post_init__(self) -> None:
        required(self.schema_id, "schema_id")
        validate_version(self.version)
        names = [item.name for item in self.fields]
        if len(names) != len(set(names)):
            raise ValueError("schema field names must be unique")
        object.__setattr__(self, "compatibility", frozen_map(self.compatibility))

    @property
    def allowed_fields(self) -> frozenset[str]:
        return frozenset(item.name for item in self.fields)


@dataclass(frozen=True, slots=True)
class DataModel:
    model_id: str
    name: str
    description: str
    scope: Scope
    owner: str
    version: str
    schema_reference: str
    repository_reference: str
    storage_reference: str
    lifecycle: Lifecycle = Lifecycle.DRAFT
    validation_status: ValidationStatus = ValidationStatus.UNKNOWN
    integrity_status: IntegrityStatus = IntegrityStatus.UNKNOWN
    retention_policy_reference: str | None = None
    security_policy_reference: str | None = None
    health: Health = field(default_factory=Health)
    metrics: Mapping[str, float] = field(default_factory=frozen_map)
    audit: tuple[str, ...] = ()
    tags: frozenset[str] = frozenset()
    safe_metadata: Mapping[str, Any] = field(default_factory=frozen_map)
    created_at: datetime = field(default_factory=now_utc)
    updated_at: datetime = field(default_factory=now_utc)

    def __post_init__(self) -> None:
        for value, name in (
            (self.model_id, "model_id"),
            (self.name, "name"),
            (self.owner, "owner"),
        ):
            required(value, name)
        validate_version(self.version)
        validate_safe_metadata(self.safe_metadata)
        object.__setattr__(self, "metrics", frozen_map(self.metrics))
        object.__setattr__(self, "safe_metadata", frozen_map(self.safe_metadata))


@dataclass(frozen=True, slots=True)
class DataRecord:
    record_id: str
    model_reference: str
    scope: Scope
    version: str
    schema_version: str
    payload_reference: str
    payload_hash: str
    integrity_status: IntegrityStatus = IntegrityStatus.UNKNOWN
    lifecycle: Lifecycle = Lifecycle.DRAFT
    created_at: datetime = field(default_factory=now_utc)
    updated_at: datetime = field(default_factory=now_utc)
    audit_reference: str | None = None
    safe_metadata: Mapping[str, Any] = field(default_factory=frozen_map)

    def __post_init__(self) -> None:
        required(self.record_id, "record_id")
        validate_version(self.version)
        validate_version(self.schema_version)
        if not self.payload_reference.startswith(("payload://", "ref://")):
            raise ValueError("sensitive payload must be reference-only")
        if not re.fullmatch(r"[0-9a-f]{64}", self.payload_hash):
            raise ValueError("payload_hash must be a SHA-256 hex digest")
        validate_safe_metadata(self.safe_metadata)
        object.__setattr__(self, "safe_metadata", frozen_map(self.safe_metadata))


@dataclass(frozen=True, slots=True)
class RepositoryDefinition:
    repository_id: str
    scope: Scope
    version: str
    model_references: tuple[str, ...] = ()
    capabilities: frozenset[str] = frozenset(
        {
            "get",
            "list",
            "filter",
            "sort",
            "paginate",
            "count",
            "exists",
            "snapshot",
            "history",
            "integrity-check",
            "validation",
        }
    )

    def __post_init__(self) -> None:
        required(self.repository_id, "repository_id")
        validate_version(self.version)


@dataclass(frozen=True, slots=True)
class StorageAdapter:
    adapter_id: str
    scope: Scope
    kind: StorageKind
    version: str
    connection_reference: str | None = None
    available: bool = True
    ready: bool = True
    diagnostics: Mapping[str, Any] = field(default_factory=frozen_map)

    def __post_init__(self) -> None:
        validate_version(self.version)
        if self.connection_reference and "://" in self.connection_reference:
            if not self.connection_reference.startswith(
                ("file://", "sqlite://", "ref://")
            ):
                raise ValueError("external storage connections are prohibited")
        validate_safe_metadata(self.diagnostics)
        object.__setattr__(self, "diagnostics", frozen_map(self.diagnostics))


@dataclass(frozen=True, slots=True)
class Filter:
    field: str
    operator: FilterOperator
    value: Any


@dataclass(frozen=True, slots=True)
class SortField:
    field: str
    direction: SortDirection = SortDirection.ASCENDING


@dataclass(frozen=True, slots=True)
class Pagination:
    offset: int = 0
    page_size: int = 50
    cursor_reference: str | None = None
    include_total: bool = False

    def __post_init__(self) -> None:
        if self.offset < 0 or not 1 <= self.page_size <= MAX_PAGE_SIZE:
            raise ValueError(f"page size must be between 1 and {MAX_PAGE_SIZE}")


@dataclass(frozen=True, slots=True)
class DataQuery:
    query_id: str
    model_reference: str
    scope: Scope
    filters: tuple[Filter, ...] = ()
    sort_order: tuple[SortField, ...] = ()
    pagination: Pagination = field(default_factory=Pagination)
    projection_fields: tuple[str, ...] = ()
    time_range: tuple[datetime, datetime] | None = None
    maximum_results: int = 100
    timeout_ms: int = 1000
    audit_reference: str | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.maximum_results <= MAX_RESULTS:
            raise ValueError(f"maximum_results must be between 1 and {MAX_RESULTS}")
        if not 1 <= self.timeout_ms <= 30_000:
            raise ValueError("timeout_ms must be between 1 and 30000")
        if len(self.sort_order) > MAX_SORT_FIELDS:
            raise ValueError("too many sort fields")
        if self.time_range:
            start, end = self.time_range
            if end < start or (end - start).days > MAX_TIME_RANGE_DAYS:
                raise ValueError("time range is invalid or unbounded")


@dataclass(frozen=True, slots=True)
class IndexDefinition:
    index_id: str
    scope: Scope
    version: str
    kind: str
    fields: tuple[str, ...]
    unique: bool = False
    planning_only: bool = True


@dataclass(frozen=True, slots=True)
class TransactionMetadata:
    transaction_id: str
    scope: Scope
    repository_references: tuple[str, ...]
    isolation_metadata: str
    status: str
    started_at: datetime = field(default_factory=now_utc)
    completed_at: datetime | None = None
    rollback_reference: str | None = None
    audit_reference: str | None = None
    simulated: bool = True
    distributed: bool = False


@dataclass(frozen=True, slots=True)
class Snapshot:
    snapshot_id: str
    repository_reference: str
    model_reference: str
    scope: Scope
    version: str
    schema_version: str
    record_count: int
    data_reference: str
    data_hash: str
    integrity_status: IntegrityStatus
    created_at: datetime = field(default_factory=now_utc)
    retention_reference: str | None = None
    audit_reference: str | None = None

    def __post_init__(self) -> None:
        if self.record_count < 0 or self.record_count > MAX_RESULTS:
            raise ValueError("snapshot record count is unbounded")
        if not self.data_reference.startswith(("snapshot://", "ref://")):
            raise ValueError("snapshot payload must be reference-only")


@dataclass(frozen=True, slots=True)
class VersionMetadata:
    subject_reference: str
    version: str
    effective_date: datetime
    superseded_by: str | None = None
    change_reason: str = ""
    change_history: tuple[str, ...] = ()
    deprecation_metadata: Mapping[str, Any] = field(default_factory=frozen_map)


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    policy_id: str
    scope: Scope
    version: str
    retention_kind: str
    duration_days: int
    archive_rule: str | None = None
    review_required: bool = True
    legal_hold: bool = False
    expiry_metadata: Mapping[str, Any] = field(default_factory=frozen_map)
    audit_reference: str | None = None
    destructive_purge: bool = False


@dataclass(frozen=True, slots=True)
class ArchivePlan:
    plan_id: str
    scope: Scope
    source_reference: str
    record_scope: str
    snapshot_reference: str | None
    retention_reference: str
    integrity_reference: str
    validation_status: ValidationStatus
    approval_reference: str | None
    status: str
    audit_reference: str | None = None
    executable: bool = False


@dataclass(frozen=True, slots=True)
class MigrationAssessment:
    assessment_id: str
    scope: Scope
    source_schema: str
    target_schema: str
    data_mapping: Mapping[str, str]
    compatibility_valid: bool
    integrity_valid: bool
    migration_steps: tuple[str, ...]
    rollback_plan: tuple[str, ...]
    risk_summary: str
    approval_reference: str | None
    readiness_status: str
    audit_reference: str | None = None
    executable: bool = False


def payload_digest(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def serialize(value: Any) -> Any:
    if is_dataclass(value):
        return {
            item.name: serialize(getattr(value, item.name)) for item in fields(value)
        }
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]"
            if str(key).lower() in SECRET_NAMES
            else serialize(item)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list, set, frozenset)):
        return [serialize(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


__all__ = tuple(name for name in globals() if not name.startswith("_"))
