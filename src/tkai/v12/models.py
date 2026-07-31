"""Immutable and safe metadata contracts for TKAI V12."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any

MAX_REFERENCES = 128
MAX_METADATA_ITEMS = 64
MAX_TEXT_LENGTH = 4096
SECRET_MARKERS = frozenset(
    {
        "api_key",
        "apikey",
        "authorization",
        "cookie",
        "credential",
        "password",
        "private_key",
        "proxy_password",
        "secret",
        "session",
        "system_message",
        "hidden_prompt",
        "chain_of_thought",
        "scratchpad",
        "token",
    }
)


class AgentType(str, Enum):
    SYSTEM = "System Agent"
    FRAMEWORK = "Framework Agent"
    CAPABILITY = "Capability Agent"
    SERVICE = "Service Agent"
    MODULE = "Module Agent"
    VALIDATION = "Validation Agent"
    DIAGNOSTIC = "Diagnostic Agent"
    KNOWLEDGE = "Knowledge Agent"
    REASONING = "Reasoning Agent"
    PLANNING = "Planning Agent"
    OPERATIONS_REFERENCE = "Operations Reference Agent"
    RECOVERY_REFERENCE = "Recovery Reference Agent"
    TEST = "Test Agent"
    MOCK = "Mock Agent"


class Lifecycle(str, Enum):
    DRAFT = "Draft"
    REGISTERED = "Registered"
    VALIDATING = "Validating"
    READY_REFERENCE = "Ready Reference"
    OBSERVING = "Observing"
    ASSESSING = "Assessing"
    PLANNING_REFERENCE = "Planning Reference"
    REVIEW_REQUIRED = "Review Required"
    APPROVED_REFERENCE = "Approved Reference"
    PAUSED = "Paused"
    MAINTENANCE = "Maintenance"
    DEGRADED_REFERENCE = "Degraded Reference"
    RESTRICTED = "Restricted"
    DEPRECATED = "Deprecated"
    SUPERSEDED = "Superseded"
    ARCHIVED = "Archived"
    DELETED = "Deleted"


class HealthStatus(str, Enum):
    HEALTHY = "Healthy"
    READY = "Ready"
    CONDITIONALLY_READY = "Conditionally Ready"
    DEGRADED_REFERENCE = "Degraded Reference"
    MAINTENANCE = "Maintenance"
    UNAVAILABLE = "Unavailable"
    UNKNOWN = "Unknown"


class RelationshipType(str, Enum):
    DEPENDS_ON = "Depends On"
    COORDINATES_WITH = "Coordinates With"
    REFERENCES = "References"
    PROVIDES_CAPABILITY_TO = "Provides Capability To"
    REQUIRES_CAPABILITY_FROM = "Requires Capability From"
    GOVERNED_BY = "Governed By"
    TRUSTED_BY = "Trusted By"
    VERIFIED_BY = "Verified By"
    COMPATIBLE_WITH = "Compatible With"
    OBSERVED_BY = "Observed By"
    SUPERSEDES = "Supersedes"
    CONFLICTS_WITH = "Conflicts With"


class MemoryType(str, Enum):
    SHORT_TERM = "Short-Term Memory"
    LONG_TERM = "Long-Term Memory"
    WORKING = "Working Memory"
    EPISODIC = "Episodic Memory"
    SEMANTIC = "Semantic Memory"
    PROCEDURAL = "Procedural Memory"
    CONTEXT = "Context Memory"
    KNOWLEDGE = "Knowledge Memory"
    DIAGNOSTIC = "Diagnostic Memory"
    AUDIT_REFERENCE = "Audit Memory Reference"


class WorkflowNodeType(str, Enum):
    REFERENCE = "Reference"
    VALIDATION = "Validation"
    ASSESSMENT = "Assessment"
    REVIEW = "Review"
    APPROVAL_REFERENCE = "Approval Reference"
    DECISION_REFERENCE = "Decision Reference"
    PLANNING_REFERENCE = "Planning Reference"
    DIAGNOSTIC = "Diagnostic"
    HEALTH = "Health"
    AUDIT = "Audit"
    MANUAL_STEP_REFERENCE = "Manual Step Reference"


def _bounded(values: tuple[str, ...]) -> None:
    if len(values) > MAX_REFERENCES:
        raise ValueError(f"reference count exceeds {MAX_REFERENCES}")
    if any(not value or len(value) > 256 for value in values):
        raise ValueError("references must be non-empty and at most 256 characters")


def validate_safe_metadata(metadata: dict[str, Any]) -> MappingProxyType[str, Any]:
    if len(metadata) > MAX_METADATA_ITEMS:
        raise ValueError("safe metadata item limit exceeded")
    result: dict[str, Any] = {}
    for key, value in metadata.items():
        normalized = key.lower().replace("-", "_")
        if any(marker in normalized for marker in SECRET_MARKERS):
            raise ValueError(
                f"secret-bearing or private metadata field rejected: {key}"
            )
        if isinstance(value, str) and len(value) > MAX_TEXT_LENGTH:
            raise ValueError(f"metadata value too large: {key}")
        if isinstance(value, dict):
            value = dict(validate_safe_metadata(value))
        elif not isinstance(value, (str, int, float, bool, tuple, list, type(None))):
            raise ValueError(f"unsafe metadata value type: {key}")
        result[key] = value
    return MappingProxyType(result)


@dataclass(frozen=True, kw_only=True)
class MetadataProfile:
    id: str
    name: str
    version: str = "12.0.0"
    owner: str = "local"
    tenant_reference: str = "default"
    workspace_reference: str = "default"
    namespace: str = "default"
    dependency_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ()
    governance_references: tuple[str, ...] = ()
    trust_references: tuple[str, ...] = ()
    integrity_references: tuple[str, ...] = ()
    security_references: tuple[str, ...] = ()
    lifecycle: Lifecycle = Lifecycle.DRAFT
    health: HealthStatus = HealthStatus.UNKNOWN
    safe_metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.id or not self.name:
            raise ValueError("id and name are required")
        for references in (
            self.dependency_references,
            self.compatibility_references,
            self.governance_references,
            self.trust_references,
            self.integrity_references,
            self.security_references,
        ):
            _bounded(references)
        object.__setattr__(
            self, "safe_metadata", validate_safe_metadata(self.safe_metadata)
        )

    @property
    def isolation_key(self) -> tuple[str, str, str]:
        return self.tenant_reference, self.workspace_reference, self.namespace

    def projection(self) -> dict[str, Any]:
        data = {item.name: getattr(self, item.name) for item in fields(self)}
        data["lifecycle"] = self.lifecycle.value
        data["health"] = self.health.value
        data["safe_metadata"] = dict(self.safe_metadata)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        data["read_only"] = True
        data["execution_enabled"] = False
        return data


@dataclass(frozen=True, kw_only=True)
class AgentProfile(MetadataProfile):
    agent_type: AgentType = AgentType.SYSTEM
    role_references: tuple[str, ...] = ()
    permission_references: tuple[str, ...] = ()
    skill_references: tuple[str, ...] = ()
    plugin_references: tuple[str, ...] = ()
    model_references: tuple[str, ...] = ()
    memory_references: tuple[str, ...] = ()
    knowledge_references: tuple[str, ...] = ()
    context_references: tuple[str, ...] = ()
    relationship_references: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class MemoryProfile(MetadataProfile):
    memory_type: MemoryType
    subject_reference: str
    context_references: tuple[str, ...] = ()
    source_references: tuple[str, ...] = ()
    knowledge_references: tuple[str, ...] = ()
    provenance_references: tuple[str, ...] = ()
    lineage_references: tuple[str, ...] = ()
    retention_metadata: str = "bounded"
    expiration_metadata: str | None = None


@dataclass(frozen=True, kw_only=True)
class SkillProfile(MetadataProfile):
    description: str = ""
    category: str = "reference"
    capability_references: tuple[str, ...] = ()
    contract_references: tuple[str, ...] = ()
    interface_references: tuple[str, ...] = ()
    validation_references: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class PluginProfile(SkillProfile):
    package_reference: str = ""
    module_references: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class ModelProfile(MetadataProfile):
    provider_reference: str = "local-reference"
    capability_references: tuple[str, ...] = ()
    context_limits_metadata: int = 0
    input_contract_references: tuple[str, ...] = ()
    output_contract_references: tuple[str, ...] = ()
    safety_references: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class KnowledgeProfile(MetadataProfile):
    source_references: tuple[str, ...] = ()
    graph_references: tuple[str, ...] = ()
    taxonomy_references: tuple[str, ...] = ()
    ontology_references: tuple[str, ...] = ()
    provenance_references: tuple[str, ...] = ()
    lineage_references: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class Relationship:
    source_reference: str
    target_reference: str
    relationship_type: RelationshipType
    tenant_reference: str = "default"
    workspace_reference: str = "default"
    namespace: str = "default"


@dataclass(frozen=True, kw_only=True)
class WorkflowNode:
    id: str
    node_type: WorkflowNodeType
    reference: str


@dataclass(frozen=True, kw_only=True)
class WorkflowEdge:
    source: str
    target: str
    relationship: str = "precedes"


@dataclass(frozen=True, kw_only=True)
class WorkflowProfile(MetadataProfile):
    nodes: tuple[WorkflowNode, ...] = ()
    edges: tuple[WorkflowEdge, ...] = ()
    preconditions: tuple[str, ...] = ()
    postconditions: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class ContractProfile(MetadataProfile):
    contract_type: str
    schema_references: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class InterfaceProfile(MetadataProfile):
    method_references: tuple[str, ...] = ()
    parameter_references: tuple[str, ...] = ()
    return_references: tuple[str, ...] = ()
    error_references: tuple[str, ...] = ()
    compatibility_rules: tuple[str, ...] = ()
    deprecation_metadata: str | None = None
