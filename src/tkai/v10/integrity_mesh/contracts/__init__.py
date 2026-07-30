"""Immutable contracts for the TKAI V10 Sovereign Integrity Mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from tkai.v10.contracts import Scope


class SubjectType(str, Enum):
    FRAMEWORK = "framework"
    CAPABILITY = "capability"
    SERVICE = "service"
    MODULE = "module"
    EXTENSION = "extension"
    RUNTIME_REFERENCE = "runtime_reference"
    CONFIGURATION = "configuration"
    STORAGE = "storage"
    DASHBOARD = "dashboard"
    AI_STUDIO = "ai_studio"
    API = "api"
    OPENAPI = "openapi"
    RELEASE_ARTIFACT = "release_artifact"
    PACKAGE = "package"
    MANIFEST = "manifest"


class EvidenceType(str, Enum):
    HASH = "hash"
    MANIFEST = "manifest"
    PACKAGE = "package"
    BUILD = "build"
    RELEASE = "release"
    VALIDATION = "validation"
    COMPATIBILITY = "compatibility"
    DEPENDENCY = "dependency"
    AUDIT = "audit"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    WARNING = "warning"
    FAILED = "failed"
    UNKNOWN = "unknown"


class RelationshipType(str, Enum):
    DEPENDS_ON = "depends_on"
    VERIFIES = "verifies"
    PROTECTS = "protects"
    REFERENCES = "references"
    CONFIRMS = "confirms"
    SUPERSEDES = "supersedes"


class DependencyIssueType(str, Enum):
    MISSING_DEPENDENCY = "missing_dependency"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    VERSION_MISMATCH = "version_mismatch"
    CONTRACT_MISMATCH = "contract_mismatch"
    INTERFACE_MISMATCH = "interface_mismatch"
    COMPATIBILITY_GAP = "compatibility_gap"
    INTEGRITY_GAP = "integrity_gap"


@dataclass(frozen=True)
class IntegrityProfile:
    profile_id: str
    subject_reference: str
    subject_type: SubjectType
    version: str = "10.0.0"
    hash_metadata: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )
    verification_metadata: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )
    evidence_references: tuple[str, ...] = ()
    dependency_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ()
    configuration_references: tuple[str, ...] = ()
    artifact_references: tuple[str, ...] = ()
    release_references: tuple[str, ...] = ()
    audit_references: tuple[str, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, float] = field(default_factory=lambda: MappingProxyType({}))
    safe_metadata: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class IntegritySubject:
    subject_id: str
    subject_type: SubjectType
    reference: str
    version: str = ""
    scope: Scope = field(default_factory=Scope)
    safe_metadata: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )


@dataclass(frozen=True)
class IntegrityEvidence:
    evidence_id: str
    evidence_type: EvidenceType
    subject_reference: str
    reference: str
    scope: Scope = field(default_factory=Scope)
    safe_metadata: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )
    secret_payload: bool = field(default=False, init=False)


@dataclass(frozen=True)
class VerificationReference:
    verification_id: str
    subject_reference: str
    status: VerificationStatus = VerificationStatus.UNKNOWN
    evidence_references: tuple[str, ...] = ()
    verifier_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    automatic_repair: bool = field(default=False, init=False)


@dataclass(frozen=True)
class IntegrityRelationship:
    relationship_id: str
    source_reference: str
    target_reference: str
    relationship_type: RelationshipType
    scope: Scope = field(default_factory=Scope)
    reference_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class DependencyIntegrity:
    dependency_id: str
    subject_reference: str
    dependency_reference: str
    issue_type: DependencyIssueType
    details_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    reference_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class CompatibilityIntegrity:
    compatibility_id: str
    source_generation: str
    subject_reference: str
    target_generation: str = "v10"
    status: VerificationStatus = VerificationStatus.UNKNOWN
    scope: Scope = field(default_factory=Scope)
    migration: bool = field(default=False, init=False)
    upgrade: bool = field(default=False, init=False)
    rollback: bool = field(default=False, init=False)


@dataclass(frozen=True)
class ReleaseIntegrity:
    release_id: str
    subject_reference: str
    build_reference: str | None = None
    manifest_reference: str | None = None
    package_reference: str | None = None
    checksum_reference: str | None = None
    artifact_reference: str | None = None
    signature_reference: str | None = None
    validation_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    signing_service: bool = field(default=False, init=False)


__all__ = (
    "CompatibilityIntegrity",
    "DependencyIntegrity",
    "DependencyIssueType",
    "EvidenceType",
    "IntegrityEvidence",
    "IntegrityProfile",
    "IntegrityRelationship",
    "IntegritySubject",
    "RelationshipType",
    "ReleaseIntegrity",
    "SubjectType",
    "VerificationReference",
    "VerificationStatus",
)
