"""Immutable metadata contracts for the V10 Sovereign Compatibility Mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from tkai.v10.contracts import Scope


class CompatibilityStatus(str, Enum):
    COMPATIBLE = "compatible"
    COMPATIBLE_WITH_CONDITIONS = "compatible_with_conditions"
    REVIEW_REQUIRED = "review_required"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


class SubjectType(str, Enum):
    FRAMEWORK = "framework"
    CAPABILITY = "capability"
    SERVICE = "service"
    MODULE = "module"
    EXTENSION = "extension"
    RUNTIME_REFERENCE = "runtime_reference"
    CONFIGURATION = "configuration"
    STORAGE = "storage"
    CONTRACT = "contract"
    INTERFACE = "interface"
    SCHEMA = "schema"
    API = "api"
    OPENAPI = "openapi"
    DASHBOARD = "dashboard"
    AI_STUDIO = "ai_studio"
    DEPLOYMENT = "deployment"
    INTEGRITY_RECORD = "integrity_record"
    TRUST_RECORD = "trust_record"
    GOVERNANCE_RECORD = "governance_record"
    RELEASE_ARTIFACT = "release_artifact"
    PACKAGE = "package"
    MANIFEST = "manifest"


class RuleType(str, Enum):
    EXACT_VERSION_MATCH = "exact_version_match"
    BACKWARD_COMPATIBLE_VERSION = "backward_compatible_version"
    FORWARD_COMPATIBLE_REFERENCE = "forward_compatible_reference"
    CONDITIONAL_COMPATIBILITY = "conditional_compatibility"
    DEPRECATED_COMPATIBILITY = "deprecated_compatibility"
    SCHEMA_ADDITIVE_CHANGE = "schema_additive_change"
    OPTIONAL_FIELD_ADDITION = "optional_field_addition"
    REQUIRED_FIELD_REMOVAL = "required_field_removal"
    REQUIRED_FIELD_ADDITION = "required_field_addition"
    TYPE_CHANGE = "type_change"
    CONTRACT_CHANGE = "contract_change"
    INTERFACE_CHANGE = "interface_change"
    DEPENDENCY_CHANGE = "dependency_change"
    CONFIGURATION_CHANGE = "configuration_change"
    STORAGE_CHANGE = "storage_change"
    API_CHANGE = "api_change"
    OPENAPI_CHANGE = "openapi_change"
    SECURITY_CHANGE = "security_change"
    GOVERNANCE_CHANGE = "governance_change"
    INTEGRITY_CHANGE = "integrity_change"
    TRUST_CHANGE = "trust_change"


@dataclass(frozen=True)
class CompatibilityProfile:
    profile_id: str
    subject_reference: str
    subject_type: SubjectType
    source_version: str
    target_version: str = "v10"
    contract_references: tuple[str, ...] = ()
    interface_references: tuple[str, ...] = ()
    schema_references: tuple[str, ...] = ()
    capability_references: tuple[str, ...] = ()
    framework_references: tuple[str, ...] = ()
    module_references: tuple[str, ...] = ()
    service_references: tuple[str, ...] = ()
    extension_references: tuple[str, ...] = ()
    configuration_references: tuple[str, ...] = ()
    storage_references: tuple[str, ...] = ()
    runtime_references: tuple[str, ...] = ()
    api_references: tuple[str, ...] = ()
    openapi_references: tuple[str, ...] = ()
    dashboard_references: tuple[str, ...] = ()
    ai_studio_references: tuple[str, ...] = ()
    deployment_references: tuple[str, ...] = ()
    integrity_references: tuple[str, ...] = ()
    trust_references: tuple[str, ...] = ()
    governance_references: tuple[str, ...] = ()
    rule_references: tuple[str, ...] = ()
    assessment_references: tuple[str, ...] = ()
    gap_references: tuple[str, ...] = ()
    conflict_references: tuple[str, ...] = ()
    plan_references: tuple[str, ...] = ()
    validation_references: tuple[str, ...] = ()
    audit_references: tuple[str, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, float] = field(default_factory=lambda: MappingProxyType({}))
    safe_metadata: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class CompatibilitySubject:
    subject_id: str
    subject_type: SubjectType
    version: str
    reference: str
    safe_metadata: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )
    scope: Scope = field(default_factory=Scope)
    reference_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class ContractMetadata:
    contract_id: str
    contract_version: str
    required_fields: tuple[str, ...] = ()
    optional_fields: tuple[str, ...] = ()
    input_references: tuple[str, ...] = ()
    output_references: tuple[str, ...] = ()
    error_references: tuple[str, ...] = ()
    security_references: tuple[str, ...] = ()
    governance_references: tuple[str, ...] = ()
    integrity_references: tuple[str, ...] = ()
    compatibility_rules: tuple[str, ...] = ()
    deprecation_metadata: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )
    executable: bool = field(default=False, init=False)


@dataclass(frozen=True)
class InterfaceMetadata:
    interface_id: str
    interface_version: str
    method_references: tuple[str, ...] = ()
    parameter_references: tuple[str, ...] = ()
    return_references: tuple[str, ...] = ()
    error_references: tuple[str, ...] = ()
    lifecycle: str = "active"
    compatibility_rules: tuple[str, ...] = ()
    deprecation_metadata: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )
    invocable: bool = field(default=False, init=False)


@dataclass(frozen=True)
class SchemaMetadata:
    schema_id: str
    schema_version: str
    field_references: tuple[str, ...] = ()
    required_fields: tuple[str, ...] = ()
    optional_fields: tuple[str, ...] = ()
    type_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    compatibility_rules: tuple[str, ...] = ()
    deprecation_metadata: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )
    mutable: bool = field(default=False, init=False)


@dataclass(frozen=True)
class CompatibilityRule:
    rule_id: str
    rule_type: RuleType
    source_value: str | None = None
    target_value: str | None = None
    status: CompatibilityStatus = CompatibilityStatus.UNKNOWN
    conditions: tuple[str, ...] = ()
    metadata_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class Assessment:
    assessment_id: str
    subject_reference: str
    status: CompatibilityStatus
    findings: tuple[str, ...] = ()
    rule_references: tuple[str, ...] = ()
    advisory: bool = field(default=True, init=False)


@dataclass(frozen=True)
class Gap:
    gap_id: str
    subject_reference: str
    kind: str
    missing_reference: str


@dataclass(frozen=True)
class Conflict:
    conflict_id: str
    subject_reference: str
    kind: str
    source_reference: str
    target_reference: str


@dataclass(frozen=True)
class CompatibilityPlan:
    plan_id: str
    subject_reference: str
    current_version: str
    target_version: str
    required_compatibility_actions: tuple[str, ...] = ()
    required_reviews: tuple[str, ...] = ()
    required_approvals: tuple[str, ...] = ()
    required_validations: tuple[str, ...] = ()
    migration_requirement_reference: str | None = None
    upgrade_requirement_reference: str | None = None
    rollback_requirement_reference: str | None = None
    risk_summary: str = ""
    limitations: tuple[str, ...] = ()
    status: str = "advisory"
    audit_reference: str | None = None
    applicable: bool = field(default=False, init=False)


@dataclass(frozen=True)
class Negotiation:
    negotiation_id: str
    source_reference: str
    target_reference: str
    source_version: str
    target_version: str
    applicable_rules: tuple[str, ...] = ()
    compatible_features: tuple[str, ...] = ()
    conditional_features: tuple[str, ...] = ()
    incompatible_features: tuple[str, ...] = ()
    missing_references: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    required_reviews: tuple[str, ...] = ()
    required_approvals: tuple[str, ...] = ()
    required_validation: tuple[str, ...] = ()
    risk_summary: str = ""
    confidence: float = 0.0
    limitations: tuple[str, ...] = ()
    result_status: CompatibilityStatus = CompatibilityStatus.UNKNOWN
    version: str = "1"
    audit_reference: str | None = None
    metadata_only: bool = field(default=True, init=False)
