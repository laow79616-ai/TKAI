"""Immutable, secret-safe contracts for the V7 configuration framework."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any

SECRET_NAMES = frozenset(
    {"api_key", "cookie", "password", "proxy_credentials", "secret", "session", "token"}
)
REFERENCE_PATTERN = re.compile(r"^(secret|vault|env|file-ref)://[A-Za-z0-9._/@:-]+$")
SEMVER_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def frozen_map(value: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


def is_secret_field(name: str) -> bool:
    lowered = name.lower()
    return any(part in lowered for part in SECRET_NAMES)


def is_secret_reference(value: object) -> bool:
    return isinstance(value, str) and bool(REFERENCE_PATTERN.fullmatch(value))


def safe_value(name: str, value: object) -> object:
    if is_secret_field(name):
        return value if is_secret_reference(value) else "[REDACTED]"
    return value


def serialize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return {
            item.name: serialize(getattr(value, item.name)) for item in fields(value)
        }
    if isinstance(value, Mapping):
        return {str(k): serialize(safe_value(str(k), v)) for k, v in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [serialize(item) for item in value]
    return value


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"
    LOCAL_WINDOWS = "local-windows"
    LOCAL_OFFLINE = "local-offline"
    RECOVERY = "recovery"
    MAINTENANCE = "maintenance"
    CUSTOM = "custom"


class Lifecycle(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID = "invalid"
    ACTIVE_REFERENCE = "active-reference"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ValidationStatus(str, Enum):
    NOT_VALIDATED = "not-validated"
    VALID = "valid"
    INVALID = "invalid"


class SourceKind(str, Enum):
    BUILTIN_DEFAULTS = "built-in-defaults"
    COMPATIBILITY_DEFAULTS = "compatibility-defaults"
    LOCAL_FILE = "local-file"
    TENANT_REFERENCE = "tenant-reference"
    WORKSPACE_REFERENCE = "workspace-reference"
    ENVIRONMENT_VARIABLE = "environment-variable"
    COMMAND_LINE_METADATA = "command-line-metadata"
    LOCAL_PROFILE_REFERENCE = "local-profile-reference"
    COMPATIBILITY_ADAPTER = "compatibility-adapter"
    TEST_OVERRIDE = "test-override"


@dataclass(frozen=True, slots=True)
class Scope:
    tenant: str
    workspace: str
    namespace: str

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.namespace)):
            raise ValueError("tenant, workspace, and namespace are required")


@dataclass(frozen=True, slots=True)
class VersionInfo:
    version: str
    effective_date: datetime = field(default_factory=now_utc)
    superseded_by: str | None = None
    change_reason: str = ""
    change_history: tuple[str, ...] = ()
    deprecation_metadata: Mapping[str, Any] = field(default_factory=frozen_map)

    def __post_init__(self) -> None:
        if not SEMVER_PATTERN.fullmatch(self.version):
            raise ValueError("version must use semantic versioning")
        object.__setattr__(
            self, "deprecation_metadata", frozen_map(self.deprecation_metadata)
        )


@dataclass(frozen=True, slots=True)
class ConfigurationDefinition:
    configuration_id: str
    name: str
    description: str
    namespace: str
    owner: str
    version: str
    environment: Environment
    profile: str
    scope: Scope
    source_references: tuple[str, ...] = ()
    schema_reference: str | None = None
    default_references: tuple[str, ...] = ()
    override_references: tuple[str, ...] = ()
    effective_value_references: Mapping[str, object] = field(default_factory=frozen_map)
    lifecycle: Lifecycle = Lifecycle.DRAFT
    validation_status: ValidationStatus = ValidationStatus.NOT_VALIDATED
    health: str = "unknown"
    metrics: Mapping[str, float] = field(default_factory=frozen_map)
    audit: tuple[str, ...] = ()
    tags: frozenset[str] = frozenset()
    safe_metadata: Mapping[str, Any] = field(default_factory=frozen_map)
    created_at: datetime = field(default_factory=now_utc)
    updated_at: datetime = field(default_factory=now_utc)

    def __post_init__(self) -> None:
        if self.namespace != self.scope.namespace:
            raise ValueError("configuration namespace must match scope")
        if not SEMVER_PATTERN.fullmatch(self.version):
            raise ValueError("configuration version must use semantic versioning")
        for name, value in self.effective_value_references.items():
            if is_secret_field(name) and not is_secret_reference(value):
                raise ValueError(f"secret field must be reference-only: {name}")
        object.__setattr__(
            self,
            "effective_value_references",
            frozen_map(self.effective_value_references),
        )
        object.__setattr__(self, "metrics", frozen_map(self.metrics))
        object.__setattr__(self, "safe_metadata", frozen_map(self.safe_metadata))


@dataclass(frozen=True, slots=True)
class SourceDefinition:
    source_id: str
    kind: SourceKind
    version: str
    scope: Scope
    environment: Environment
    profile: str
    field_references: Mapping[str, object] = field(default_factory=frozen_map)
    available: bool = True
    path_reference: str | None = None
    safe_metadata: Mapping[str, Any] = field(default_factory=frozen_map)

    def __post_init__(self) -> None:
        if not SEMVER_PATTERN.fullmatch(self.version):
            raise ValueError("source version must use semantic versioning")
        for name, value in self.field_references.items():
            if is_secret_field(name) and not is_secret_reference(value):
                raise ValueError(f"secret field must be reference-only: {name}")
        object.__setattr__(self, "field_references", frozen_map(self.field_references))
        object.__setattr__(self, "safe_metadata", frozen_map(self.safe_metadata))


@dataclass(frozen=True, slots=True)
class PrecedenceRule:
    rule_id: str
    profile_id: str
    version: str
    ordered_sources: tuple[SourceKind, ...]
    explanation: str

    def __post_init__(self) -> None:
        if len(self.ordered_sources) != len(set(self.ordered_sources)):
            raise ValueError("precedence sources must be unique")
        if not SEMVER_PATTERN.fullmatch(self.version):
            raise ValueError("precedence version must use semantic versioning")


@dataclass(frozen=True, slots=True)
class EnvironmentProfile:
    profile_id: str
    environment: Environment
    allowed_sources: frozenset[SourceKind]
    precedence_rule: PrecedenceRule
    validation_policy: Mapping[str, Any] = field(default_factory=frozen_map)
    security_policy: Mapping[str, Any] = field(default_factory=frozen_map)
    compatibility_policy: Mapping[str, Any] = field(default_factory=frozen_map)
    lifecycle: Lifecycle = Lifecycle.REGISTERED
    metadata: Mapping[str, Any] = field(default_factory=frozen_map)
    custom_name: str | None = None

    def __post_init__(self) -> None:
        if self.environment is Environment.CUSTOM and not self.custom_name:
            raise ValueError("custom profiles require a bounded custom name")
        if not set(self.precedence_rule.ordered_sources).issubset(self.allowed_sources):
            raise ValueError("precedence contains a source outside the allowlist")
        for name in (
            "validation_policy",
            "security_policy",
            "compatibility_policy",
            "metadata",
        ):
            object.__setattr__(self, name, frozen_map(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class FieldDefinition:
    name: str
    type_name: str
    required: bool = False
    allowed_values: tuple[object, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    format_pattern: str | None = None
    secret: bool = False
    immutable: bool = False
    deprecated: bool = False
    safe_default: object | None = None


@dataclass(frozen=True, slots=True)
class SchemaDefinition:
    schema_id: str
    namespace: str
    version: str
    fields: tuple[FieldDefinition, ...]
    compatibility_metadata: Mapping[str, Any] = field(default_factory=frozen_map)

    def __post_init__(self) -> None:
        if not SEMVER_PATTERN.fullmatch(self.version):
            raise ValueError("schema version must use semantic versioning")
        if len({item.name for item in self.fields}) != len(self.fields):
            raise ValueError("schema fields must be unique")
        object.__setattr__(
            self, "compatibility_metadata", frozen_map(self.compatibility_metadata)
        )


@dataclass(frozen=True, slots=True)
class DefaultArtifact:
    default_id: str
    namespace: str
    environment: Environment
    profile: str
    version: str
    field_references: Mapping[str, object]
    provenance: str
    explanation: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "field_references", frozen_map(self.field_references))


@dataclass(frozen=True, slots=True)
class OverrideArtifact:
    override_id: str
    scope: Scope
    source: SourceKind
    target_namespace: str
    field_references: Mapping[str, object]
    reason: str
    owner: str
    expiry: datetime | None = None
    approval_reference: str | None = None
    validation_status: ValidationStatus = ValidationStatus.NOT_VALIDATED
    audit_reference: str | None = None

    def __post_init__(self) -> None:
        for name, value in self.field_references.items():
            if is_secret_field(name) and not is_secret_reference(value):
                raise ValueError(f"secret field must be reference-only: {name}")
        object.__setattr__(self, "field_references", frozen_map(self.field_references))

    @property
    def expired(self) -> bool:
        return self.expiry is not None and self.expiry <= now_utc()


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    field_reference: str | None
    message: str
    severity: str = "error"


@dataclass(frozen=True, slots=True)
class ValidationResult:
    validation_id: str
    status: ValidationStatus
    issues: tuple[ValidationIssue, ...]
    checked_rules: tuple[str, ...]
    bounded: bool = True


@dataclass(frozen=True, slots=True)
class EffectiveConfiguration:
    configuration_reference: str
    namespace: str
    environment: Environment
    profile: str
    scope: Scope
    effective_field_references: Mapping[str, object]
    source_provenance: Mapping[str, str]
    precedence_explanation: tuple[str, ...]
    validation_summary: Mapping[str, Any]
    conflict_summary: tuple[str, ...]
    compatibility_summary: Mapping[str, Any]
    security_summary: Mapping[str, Any]
    version: str
    timestamp: datetime = field(default_factory=now_utc)

    def __post_init__(self) -> None:
        for name in (
            "effective_field_references",
            "source_provenance",
            "validation_summary",
            "compatibility_summary",
            "security_summary",
        ):
            object.__setattr__(self, name, frozen_map(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class ConfigurationSnapshot:
    snapshot_id: str
    configuration_reference: str
    environment: Environment
    profile: str
    version: str
    schema_reference: str | None
    source_references: tuple[str, ...]
    effective_value_hash: str
    integrity_status: str
    validation_status: ValidationStatus
    created_at: datetime
    audit_reference: str


@dataclass(frozen=True, slots=True)
class DiffEntry:
    field_reference: str
    change: str
    before_reference: object
    after_reference: object
    provenance_change: str | None = None
    validation_change: str | None = None
    compatibility_change: str | None = None
    security_impact: str = "none"


@dataclass(frozen=True, slots=True)
class ConfigurationDiff:
    diff_id: str
    before_reference: str
    after_reference: str
    entries: tuple[DiffEntry, ...]
    truncated: bool = False


@dataclass(frozen=True, slots=True)
class ChangePlan:
    change_plan_id: str
    current_configuration_reference: str
    proposed_configuration_reference: str
    diff_reference: str
    validation_reference: str
    compatibility_reference: str
    security_review_reference: str
    risk_summary: str
    rollback_reference: str
    approval_reference: str | None
    status: str
    audit_reference: str
    advisory_only: bool = True


@dataclass(frozen=True, slots=True)
class MigrationAssessment:
    assessment_id: str
    source_mapping: Mapping[str, str]
    schema_mapping: Mapping[str, str]
    compatibility_valid: bool
    proposed_steps: tuple[str, ...]
    rollback_plan: tuple[str, ...]
    ready: bool
    audit_reference: str
    automatic: bool = False
