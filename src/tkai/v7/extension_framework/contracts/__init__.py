"""Immutable contracts for the internal V7 extension metadata plane."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any

SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
CHECKSUM_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")
SECRET_NAMES = frozenset(
    {"api_key", "cookie", "credential", "password", "private_key", "secret", "token"}
)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def frozen_map(value: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


def is_secret_name(name: str) -> bool:
    lowered = name.lower()
    return any(item in lowered for item in SECRET_NAMES)


def serialize(value: Any) -> Any:
    """Serialize contracts while filtering values with secret-like keys."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return {
            item.name: serialize(getattr(value, item.name)) for item in fields(value)
        }
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]" if is_secret_name(str(key)) else serialize(item)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list, set, frozenset)):
        return [serialize(item) for item in value]
    return value


def validate_identifier(value: str, label: str) -> None:
    if not IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(f"{label} must be a bounded lowercase identifier")


def validate_version(value: str, label: str = "version") -> None:
    if not SEMVER_PATTERN.fullmatch(value):
        raise ValueError(f"{label} must use semantic versioning")


class Lifecycle(str, Enum):
    DISCOVERED = "discovered"
    REGISTERED = "registered"
    VALIDATED = "validated"
    COMPATIBLE = "compatible"
    AVAILABLE = "available"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"
    RETIRED = "retired"
    ARCHIVED = "archived"


class ExtensionStatus(str, Enum):
    UNKNOWN = "unknown"
    VALID = "valid"
    INVALID = "invalid"
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    AVAILABLE = "available"
    DISABLED = "disabled"


class ValidationStatus(str, Enum):
    NOT_VALIDATED = "not-validated"
    VALID = "valid"
    INVALID = "invalid"


class VerificationStatus(str, Enum):
    NOT_VERIFIED = "not-verified"
    VERIFIED = "verified"
    FAILED = "failed"
    UNTRUSTED = "untrusted"


@dataclass(frozen=True, slots=True)
class Scope:
    tenant: str
    workspace: str
    namespace: str = "extensions"

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.namespace)):
            raise ValueError("tenant, workspace, and namespace are required")


@dataclass(frozen=True, slots=True)
class Dependency:
    extension_id: str
    version_constraint: str = "*"
    optional: bool = False
    required_capabilities: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        validate_identifier(self.extension_id, "dependency extension_id")


@dataclass(frozen=True, slots=True)
class Compatibility:
    platform_constraint: str = ">=7.0.0,<8.0.0"
    python_constraint: str = ">=3.10"
    required_capabilities: frozenset[str] = frozenset()
    required_interfaces: Mapping[str, str] = field(default_factory=frozen_map)
    migration_metadata: Mapping[str, Any] = field(default_factory=frozen_map)
    v6_compatible: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "required_interfaces", frozen_map(self.required_interfaces)
        )
        object.__setattr__(
            self, "migration_metadata", frozen_map(self.migration_metadata)
        )


@dataclass(frozen=True, slots=True)
class SandboxMetadata:
    policy: str = "metadata-only"
    capability_boundary: frozenset[str] = frozenset()
    permission_boundary: frozenset[str] = frozenset()
    resource_boundary: Mapping[str, Any] = field(default_factory=frozen_map)
    event_boundary: frozenset[str] = frozenset()
    state_boundary: frozenset[str] = frozenset()
    configuration_boundary: frozenset[str] = frozenset()
    executable_runtime: bool = False

    def __post_init__(self) -> None:
        if self.executable_runtime:
            raise ValueError("V7 extension sandbox is metadata-only")
        object.__setattr__(
            self, "resource_boundary", frozen_map(self.resource_boundary)
        )


@dataclass(frozen=True, slots=True)
class PackageMetadata:
    package_id: str
    version: str
    manifest_reference: str
    checksums: Mapping[str, str]
    source: str = "internal-static"
    integrity_metadata: Mapping[str, Any] = field(default_factory=frozen_map)
    version_metadata: Mapping[str, Any] = field(default_factory=frozen_map)
    source_metadata: Mapping[str, Any] = field(default_factory=frozen_map)
    installable: bool = False

    def __post_init__(self) -> None:
        validate_identifier(self.package_id, "package_id")
        validate_version(self.version)
        if self.installable:
            raise ValueError("package installation is not supported")
        if not self.checksums or any(
            not CHECKSUM_PATTERN.fullmatch(value) for value in self.checksums.values()
        ):
            raise ValueError("package checksums must contain SHA-256 metadata")
        for name in (
            "checksums",
            "integrity_metadata",
            "version_metadata",
            "source_metadata",
        ):
            object.__setattr__(self, name, frozen_map(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class SignatureMetadata:
    signature_id: str
    fingerprint: str
    algorithm: str
    verification_status: VerificationStatus = VerificationStatus.NOT_VERIFIED
    trust_metadata: Mapping[str, Any] = field(default_factory=frozen_map)
    verified_locally: bool = False
    remote_verification: bool = False

    def __post_init__(self) -> None:
        validate_identifier(self.signature_id, "signature_id")
        if self.remote_verification:
            raise ValueError("remote signature verification is not supported")
        object.__setattr__(self, "trust_metadata", frozen_map(self.trust_metadata))


@dataclass(frozen=True, slots=True)
class HealthMetadata:
    status: str = "unknown"
    checks: Mapping[str, str] = field(default_factory=frozen_map)
    updated_at: datetime = field(default_factory=now_utc)

    def __post_init__(self) -> None:
        object.__setattr__(self, "checks", frozen_map(self.checks))


@dataclass(frozen=True, slots=True)
class ExtensionManifest:
    extension_id: str
    name: str
    description: str
    category: str
    owner: str
    version: str
    scope: Scope
    plugin_ids: tuple[str, ...] = ()
    compatibility: Compatibility = field(default_factory=Compatibility)
    dependencies: tuple[Dependency, ...] = ()
    permissions: frozenset[str] = frozenset()
    capabilities: frozenset[str] = frozenset()
    interfaces: Mapping[str, str] = field(default_factory=frozen_map)
    status: ExtensionStatus = ExtensionStatus.UNKNOWN
    lifecycle: Lifecycle = Lifecycle.DISCOVERED
    metadata: Mapping[str, Any] = field(default_factory=frozen_map)
    health: HealthMetadata = field(default_factory=HealthMetadata)
    metrics: Mapping[str, float] = field(default_factory=frozen_map)
    audit: tuple[str, ...] = ()
    sandbox: SandboxMetadata = field(default_factory=SandboxMetadata)
    package: PackageMetadata | None = None
    signature: SignatureMetadata | None = None
    created_at: datetime = field(default_factory=now_utc)
    updated_at: datetime = field(default_factory=now_utc)

    def __post_init__(self) -> None:
        validate_identifier(self.extension_id, "extension_id")
        validate_version(self.version)
        if len(set(self.plugin_ids)) != len(self.plugin_ids):
            raise ValueError("plugin_ids must be unique")
        for plugin_id in self.plugin_ids:
            validate_identifier(plugin_id, "plugin_id")
        for name in ("interfaces", "metadata", "metrics"):
            object.__setattr__(self, name, frozen_map(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class PluginManifest:
    plugin_id: str
    extension_id: str
    name: str
    description: str
    category: str
    owner: str
    version: str
    scope: Scope
    compatibility: Compatibility = field(default_factory=Compatibility)
    dependencies: tuple[Dependency, ...] = ()
    permissions: frozenset[str] = frozenset()
    capabilities: frozenset[str] = frozenset()
    interfaces: Mapping[str, str] = field(default_factory=frozen_map)
    status: ExtensionStatus = ExtensionStatus.UNKNOWN
    lifecycle: Lifecycle = Lifecycle.DISCOVERED
    metadata: Mapping[str, Any] = field(default_factory=frozen_map)
    health: HealthMetadata = field(default_factory=HealthMetadata)
    metrics: Mapping[str, float] = field(default_factory=frozen_map)
    audit: tuple[str, ...] = ()
    sandbox: SandboxMetadata = field(default_factory=SandboxMetadata)

    def __post_init__(self) -> None:
        validate_identifier(self.plugin_id, "plugin_id")
        validate_identifier(self.extension_id, "extension_id")
        validate_version(self.version)
        for name in ("interfaces", "metadata", "metrics"):
            object.__setattr__(self, name, frozen_map(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    field_reference: str | None
    message: str
    severity: str = "error"


@dataclass(frozen=True, slots=True)
class ValidationResult:
    subject_id: str
    status: ValidationStatus
    issues: tuple[ValidationIssue, ...]
    checked_rules: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CompatibilityResult:
    subject_id: str
    compatible: bool
    platform: bool
    capabilities: bool
    interfaces: bool
    dependencies: bool
    reasons: tuple[str, ...]
    migration_metadata: Mapping[str, Any] = field(default_factory=frozen_map)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "migration_metadata", frozen_map(self.migration_metadata)
        )


@dataclass(frozen=True, slots=True)
class DependencyResolution:
    subject_id: str
    ordered_extension_ids: tuple[str, ...]
    missing: tuple[str, ...]
    incompatible: tuple[str, ...]
    cycles: tuple[tuple[str, ...], ...]
    satisfied: bool


__all__ = tuple(name for name in globals() if not name.startswith("_"))
