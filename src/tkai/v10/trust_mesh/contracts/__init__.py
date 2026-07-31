"""Immutable contracts for the TKAI V10 Sovereign Trust Mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType

from tkai.v10.contracts import Scope


def utc_now() -> datetime:
    """Return an aware timestamp for metadata records."""
    return datetime.now(timezone.utc)


class TrustDomainKind(str, Enum):
    """Supported reference-only trust domain classifications."""

    LOCAL_HOST = "local_host"
    TENANT = "tenant"
    WORKSPACE = "workspace"
    NAMESPACE = "namespace"
    FRAMEWORK = "framework"
    CAPABILITY = "capability"
    SERVICE = "service"
    MODULE = "module"
    EXTENSION = "extension"
    RUNTIME = "runtime"


class RelationshipStatus(str, Enum):
    """Descriptive relationship states; none grants access or trust."""

    TRUSTED = "trusted"
    RESTRICTED = "restricted"
    OBSERVED = "observed"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TrustMeshProfile:
    """Top-level metadata profile spanning federated TKAI generations."""

    profile_id: str
    version: str = "10.0.0"
    owner: str = "TKAI"
    trust_domain_references: tuple[str, ...] = ()
    identity_references: tuple[str, ...] = ()
    principal_references: tuple[str, ...] = ()
    relationship_references: tuple[str, ...] = ()
    integrity_references: tuple[str, ...] = ()
    attestation_references: tuple[str, ...] = ()
    governance_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ()
    health: str = "healthy"
    metrics: Mapping[str, float] = field(default_factory=lambda: MappingProxyType({}))
    audit: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class TrustDomainRecord:
    domain_id: str
    kind: TrustDomainKind
    name: str
    scope: Scope = field(default_factory=Scope)
    parent_reference: str | None = None
    governance_references: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True)
class IdentityRecord:
    identity_id: str
    identity_type: str
    provider_reference: str
    scope: Scope = field(default_factory=Scope)
    principal_references: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True)
class PrincipalRecord:
    principal_id: str
    identity_reference: str
    role_references: tuple[str, ...] = ()
    permission_references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class TrustRelationship:
    relationship_id: str
    source_reference: str
    target_reference: str
    status: RelationshipStatus = RelationshipStatus.UNKNOWN
    evidence_references: tuple[str, ...] = ()
    governance_references: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)
    grants_trust: bool = field(default=False, init=False)


@dataclass(frozen=True)
class IntegrityMetadata:
    integrity_id: str
    subject_reference: str
    hash_algorithm: str = "sha256"
    expected_hash: str | None = None
    observed_hash_reference: str | None = None
    verification_status: str = "unverified"
    evidence_references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)
    remote_verification: bool = field(default=False, init=False)


@dataclass(frozen=True)
class AttestationMetadata:
    attestation_id: str
    subject_reference: str
    issuer_reference: str
    attestation_type: str = "metadata"
    status: str = "registered"
    evidence_references: tuple[str, ...] = ()
    integrity_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    external_attestation: bool = field(default=False, init=False)


@dataclass(frozen=True)
class TrustScore:
    score_id: str
    subject_reference: str
    value: float
    explanation: str
    evidence_references: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    methodology_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    automatic_decision: bool = field(default=False, init=False)


@dataclass(frozen=True)
class CompatibilityMetadata:
    compatibility_id: str
    source_generation: str
    target_generation: str = "v10"
    component_reference: str = ""
    status: str = "compatible"
    limitations: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)
    automatic_migration: bool = field(default=False, init=False)


__all__ = (
    "AttestationMetadata",
    "CompatibilityMetadata",
    "IdentityRecord",
    "IntegrityMetadata",
    "PrincipalRecord",
    "RelationshipStatus",
    "TrustDomainKind",
    "TrustDomainRecord",
    "TrustMeshProfile",
    "TrustRelationship",
    "TrustScore",
)
