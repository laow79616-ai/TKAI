"""Immutable, bounded TKAI V11 Autonomous Reasoning Fabric."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any

from tkai.v11.contracts import Scope
from tkai.v11.security import authorize_scope, filter_secrets, validate_safe_metadata

VERSION = "11.0.0"
COMPATIBLE_VERSIONS = ("v6", "v7", "v8", "v9", "v10", "v11")
EVIDENCE_PROVIDERS = (
    "v11-autonomous-knowledge-graph",
    "v11-autonomous-intelligence-core",
    "v10-sovereign-knowledge-mesh",
    "v10-sovereign-integrity-mesh",
    "v10-sovereign-trust-mesh",
    "v10-sovereign-governance-mesh",
    "v10-sovereign-compatibility-mesh",
    "v10-sovereign-reasoning-mesh",
    "v9-adaptive-knowledge-mesh",
    "v9-adaptive-reasoning-mesh",
    "v8-metadata-providers",
    "v7-metadata-providers",
    "v6-metadata-providers",
)


def _empty_mapping() -> Mapping[str, object]:
    return MappingProxyType({})


class ClaimType(str, Enum):
    OBSERVATIONAL = "observational"
    DERIVED = "derived"
    COMPARATIVE = "comparative"
    COMPATIBILITY = "compatibility"
    INTEGRITY = "integrity"
    TRUST = "trust"
    GOVERNANCE = "governance"
    SECURITY = "security"
    DIAGNOSTIC = "diagnostic"
    HEALTH = "health"
    RISK = "risk"
    LIMITATION = "limitation"
    OPERATIONAL_REFERENCE = "operational-reference"
    PLANNING_REFERENCE = "planning-reference"
    DECISION_REFERENCE = "decision-reference"


class InferenceType(str, Enum):
    DEDUCTIVE_REFERENCE = "deductive-reference"
    INDUCTIVE_REFERENCE = "inductive-reference"
    COMPARATIVE_REFERENCE = "comparative-reference"
    COMPATIBILITY_REFERENCE = "compatibility-reference"
    INTEGRITY_REFERENCE = "integrity-reference"
    TRUST_REFERENCE = "trust-reference"
    GOVERNANCE_REFERENCE = "governance-reference"
    DIAGNOSTIC_REFERENCE = "diagnostic-reference"
    RISK_REFERENCE = "risk-reference"
    CONSTRAINT_REFERENCE = "constraint-reference"
    DEPENDENCY_REFERENCE = "dependency-reference"
    KNOWLEDGE_GRAPH_REFERENCE = "knowledge-graph-reference"


class UncertaintyStatus(str, Enum):
    KNOWN = "known"
    PARTIALLY_KNOWN = "partially-known"
    UNKNOWN = "unknown"
    CONFLICTING = "conflicting"
    INSUFFICIENT_EVIDENCE = "insufficient-evidence"
    OUTDATED_REFERENCE = "outdated-reference"
    UNVERIFIED_REFERENCE = "unverified-reference"
    UNSUPPORTED = "unsupported"
    MANUAL_REVIEW_REQUIRED = "manual-review-required"


class ContradictionType(str, Enum):
    CLAIM = "claim-conflict"
    PREMISE = "premise-conflict"
    EVIDENCE = "evidence-conflict"
    VERSION = "version-conflict"
    KNOWLEDGE_GRAPH = "knowledge-graph-conflict"
    COMPATIBILITY = "compatibility-conflict"
    INTEGRITY = "integrity-conflict"
    TRUST = "trust-conflict"
    GOVERNANCE = "governance-conflict"
    SECURITY = "security-conflict"
    CONFIGURATION = "configuration-conflict"
    RUNTIME_REFERENCE = "runtime-reference-conflict"
    DEPENDENCY = "dependency-conflict"


@dataclass(frozen=True)
class ReasoningContext:
    context_id: str
    subject_reference: str
    scope_summary: str
    tenant_reference: str = ""
    workspace_reference: str = ""
    namespace: str = "default"
    time_range: tuple[str, str] | None = None
    objective_references: tuple[str, ...] = ()
    knowledge_graph_references: tuple[str, ...] = ()
    policy_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    boundary_references: tuple[str, ...] = ()
    trust_references: tuple[str, ...] = ()
    integrity_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ()
    version: str = VERSION
    status: str = "registered"
    safe_metadata: Mapping[str, object] = field(default_factory=_empty_mapping)
    audit_reference: str = ""


@dataclass(frozen=True)
class Claim:
    claim_id: str
    claim_type: ClaimType
    subject_reference: str
    statement_summary: str
    status: str = "advisory"
    evidence_references: tuple[str, ...] = ()
    premise_references: tuple[str, ...] = ()
    assumption_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    alternative_references: tuple[str, ...] = ()
    confidence_reference: str = ""
    uncertainty_reference: str = ""
    contradiction_references: tuple[str, ...] = ()
    version: str = VERSION
    audit_reference: str = ""


@dataclass(frozen=True)
class Premise:
    premise_id: str
    summary: str
    source_reference: str
    evidence_references: tuple[str, ...] = ()
    knowledge_graph_references: tuple[str, ...] = ()
    integrity_reference: str = ""
    trust_reference: str = ""
    compatibility_reference: str = ""
    governance_reference: str = ""
    status: str = "registered"
    version: str = VERSION
    audit_reference: str = ""


@dataclass(frozen=True)
class EvidenceReference:
    evidence_id: str
    provider: str
    source_reference: str
    summary: str = ""
    version: str = VERSION
    audit_reference: str = ""
    read_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class InferenceReference:
    inference_id: str
    inference_type: InferenceType
    result_claim_reference: str
    premise_references: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()
    knowledge_graph_references: tuple[str, ...] = ()
    rule_reference: str = ""
    constraint_references: tuple[str, ...] = ()
    confidence_reference: str = ""
    uncertainty_reference: str = ""
    contradiction_references: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    status: str = "recorded"
    version: str = VERSION
    audit_reference: str = ""
    executable: bool = field(default=False, init=False)


@dataclass(frozen=True)
class Assumption:
    assumption_id: str
    summary: str
    scope: str
    source_reference: str = ""
    validation_status: str = "unverified"
    risk_level: str = "unknown"
    confidence_reference: str = ""
    expiration_reference: str = ""
    limitation_references: tuple[str, ...] = ()
    audit_reference: str = ""


@dataclass(frozen=True)
class Constraint:
    constraint_id: str
    kind: str
    reference: str
    limit: int | None = None
    audit_reference: str = ""


@dataclass(frozen=True)
class Alternative:
    alternative_id: str
    summary: str
    claim_references: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    knowledge_graph_references: tuple[str, ...] = ()
    impacts: Mapping[str, object] = field(default_factory=_empty_mapping)
    risk_summary: str = ""
    confidence_reference: str = ""
    uncertainty_reference: str = ""
    limitations: tuple[str, ...] = ()
    status: str = "advisory"
    audit_reference: str = ""
    automatically_selected: bool = field(default=False, init=False)


@dataclass(frozen=True)
class Contradiction:
    contradiction_id: str
    kind: ContradictionType
    reference_ids: tuple[str, ...]
    summary: str
    status: str = "unresolved"
    audit_reference: str = ""
    automatically_resolved: bool = field(default=False, init=False)


@dataclass(frozen=True)
class Confidence:
    confidence_id: str
    band: str
    value: float | None = None
    evidence_coverage: str = "unknown"
    source_quality_reference: str = ""
    knowledge_graph_coverage: str = "unknown"
    integrity_status: str = "unknown"
    trust_status: str = "unknown"
    compatibility_status: str = "unknown"
    governance_status: str = "unknown"
    contradiction_count: int = 0
    limitation_count: int = 0
    explanation_reference: str = ""


@dataclass(frozen=True)
class Uncertainty:
    uncertainty_id: str
    status: UncertaintyStatus
    summary: str = ""
    audit_reference: str = ""


@dataclass(frozen=True)
class SafeExplanation:
    explanation_id: str
    summary: str
    supporting_claim_references: tuple[str, ...] = ()
    premise_references: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()
    assumption_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    alternative_references: tuple[str, ...] = ()
    knowledge_graph_references: tuple[str, ...] = ()
    confidence_summary: str = ""
    uncertainty_summary: str = ""
    contradiction_summary: str = ""
    limitations: tuple[str, ...] = ()
    audit_reference: str = ""


@dataclass(frozen=True)
class Evaluation:
    evaluation_id: str
    kind: str
    summary: str
    status: str = "advisory"
    references: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    audit_reference: str = ""
    executable: bool = field(default=False, init=False)


@dataclass(frozen=True)
class FabricLimits:
    contexts: int = 100
    claims: int = 1000
    premises: int = 2000
    evidence: int = 2000
    inferences: int = 1000
    alternatives: int = 100
    node_references: int = 5000
    edge_references: int = 5000
    sources: int = 100
    result_size: int = 10000


@dataclass(frozen=True)
class ReasoningFabricProfile:
    fabric_profile_id: str = "tkai-v11-autonomous-reasoning-fabric"
    subject_reference: str = "tkai:v11"
    contexts: tuple[ReasoningContext, ...] = ()
    claims: tuple[Claim, ...] = ()
    premises: tuple[Premise, ...] = ()
    evidence: tuple[EvidenceReference, ...] = ()
    inferences: tuple[InferenceReference, ...] = ()
    assumptions: tuple[Assumption, ...] = ()
    constraints: tuple[Constraint, ...] = ()
    alternatives: tuple[Alternative, ...] = ()
    contradictions: tuple[Contradiction, ...] = ()
    confidence: tuple[Confidence, ...] = ()
    uncertainty: tuple[Uncertainty, ...] = ()
    explanations: tuple[SafeExplanation, ...] = ()
    evaluations: tuple[Evaluation, ...] = ()
    relationship_references: tuple[str, ...] = ()
    knowledge_graph_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = COMPATIBLE_VERSIONS
    governance_references: tuple[str, ...] = ()
    trust_references: tuple[str, ...] = ()
    integrity_references: tuple[str, ...] = ()
    validation_references: tuple[str, ...] = ()
    audit_references: tuple[str, ...] = ()
    safe_metadata: Mapping[str, object] = field(default_factory=_empty_mapping)
    version: str = VERSION
    lifecycle: str = "active"
    limits: FabricLimits = field(default_factory=FabricLimits)
    scope: Scope = field(default_factory=Scope)
    advisory: bool = field(default=True, init=False)
    deterministic: bool = field(default=True, init=False)
    read_only: bool = field(default=True, init=False)
    executable: bool = field(default=False, init=False)


class AutonomousReasoningFabric:
    """Read-only metadata coordinator with no decision or inference execution."""

    _COLLECTIONS = (
        "contexts",
        "claims",
        "premises",
        "evidence",
        "inferences",
        "assumptions",
        "constraints",
        "alternatives",
        "contradictions",
        "confidence",
        "uncertainty",
        "explanations",
        "evaluations",
    )

    def __init__(
        self,
        profile: ReasoningFabricProfile | None = None,
        *,
        scope: Scope | None = None,
    ) -> None:
        self._profile = profile or ReasoningFabricProfile()
        self._scope = scope or self._profile.scope
        authorize_scope(self._scope, self._profile.scope)
        validate_safe_metadata(self._profile.safe_metadata)
        for context in self._profile.contexts:
            validate_safe_metadata(context.safe_metadata)
        issues = self._issues()
        if issues:
            raise ValueError("; ".join(issues))

    def _issues(self) -> tuple[str, ...]:
        p, limits = self._profile, self._profile.limits
        issues: list[str] = []
        bounded = {
            "contexts": limits.contexts,
            "claims": limits.claims,
            "premises": limits.premises,
            "evidence": limits.evidence,
            "inferences": limits.inferences,
            "alternatives": limits.alternatives,
        }
        for name, limit in bounded.items():
            if len(getattr(p, name)) > limit:
                issues.append(f"{name} exceeds bounded limit {limit}")
        ids: list[str] = []
        for name in self._COLLECTIONS:
            for item in getattr(p, name):
                identity = next(
                    (getattr(item, key) for key in vars(item) if key.endswith("_id")),
                    "",
                )
                ids.append(str(identity))
        if len(ids) != len(set(ids)):
            issues.append("duplicate metadata id")
        invalid_providers = sorted(
            {item.provider for item in p.evidence} - set(EVIDENCE_PROVIDERS)
        )
        if invalid_providers:
            issues.append(f"evidence provider not allowlisted: {invalid_providers}")
        for confidence in p.confidence:
            if confidence.value is not None and not 0 <= confidence.value <= 1:
                issues.append(f"invalid confidence value: {confidence.confidence_id}")
        return tuple(sorted(issues))

    def profile(self) -> dict[str, object]:
        return {
            "fabric_profile_id": self._profile.fabric_profile_id,
            "subject_reference": self._profile.subject_reference,
            "references": {
                name: tuple(
                    next(
                        getattr(item, key) for key in vars(item) if key.endswith("_id")
                    )
                    for item in getattr(self._profile, name)
                )
                for name in self._COLLECTIONS
            },
            "relationship_references": self._profile.relationship_references,
            "knowledge_graph_references": self._profile.knowledge_graph_references,
            "compatibility_references": self._profile.compatibility_references,
            "governance_references": self._profile.governance_references,
            "trust_references": self._profile.trust_references,
            "integrity_references": self._profile.integrity_references,
            "validation_references": self._profile.validation_references,
            "audit_references": self._profile.audit_references,
            "health": self.health(),
            "metrics": self.metrics(),
            "safe_metadata": self._profile.safe_metadata,
            "version": self._profile.version,
            "lifecycle": self._profile.lifecycle,
            "advisory": True,
            "read_only": True,
            "deterministic": True,
            "executable": False,
        }

    def _items(self, name: str) -> dict[str, object]:
        items = getattr(self._profile, name)
        return {"items": items, "count": len(items), "read_only": True}

    def __getattr__(self, name: str) -> Any:
        if name in self._COLLECTIONS:
            return lambda: self._items(name)
        raise AttributeError(name)

    def relationships(self) -> dict[str, object]:
        return {"items": self._profile.relationship_references, "reference_only": True}

    def knowledge_graph(self) -> dict[str, object]:
        return {
            "references": self._profile.knowledge_graph_references,
            "providers": ("v11-autonomous-knowledge-graph",),
            "node_references": (),
            "edge_references": (),
            "graph_mutation": False,
            "graph_execution": False,
        }

    def compatibility(self) -> dict[str, object]:
        return {"versions": COMPATIBLE_VERSIONS, "migration": False, "upgrade": False}

    def governance(self) -> dict[str, object]:
        return {
            "references": self._profile.governance_references,
            "policy_execution": False,
            "automatic_approval": False,
            "review_required": True,
            "pause_aware": True,
            "maintenance_aware": True,
            "kill_switch_aware": True,
        }

    def trust(self) -> dict[str, object]:
        return {"references": self._profile.trust_references, "read_only": True}

    def integrity(self) -> dict[str, object]:
        return {
            "references": self._profile.integrity_references,
            "valid": not self._issues(),
        }

    def validation(self) -> dict[str, object]:
        return {"valid": not self._issues(), "issues": self._issues(), "bounded": True}

    def diagnostics(self) -> dict[str, object]:
        return {
            "status": "clear" if not self._issues() else "issues",
            "items": self._issues(),
            "read_only": True,
        }

    def health(self) -> dict[str, object]:
        ready = not self._issues()
        return {
            "status": "healthy" if ready else "degraded",
            "reasoning_readiness": ready,
            "reasoning_liveness": True,
            "execution_ready": False,
        }

    def metrics(self) -> dict[str, int | float]:
        p = self._profile
        values = {
            "profiles": 1,
            "contexts": len(p.contexts),
            "claims": len(p.claims),
            "premises": len(p.premises),
            "evidence_references": len(p.evidence),
            "inferences": len(p.inferences),
            "assumptions": len(p.assumptions),
            "constraints": len(p.constraints),
            "alternatives": len(p.alternatives),
            "contradictions": len(p.contradictions),
            "explanations": len(p.explanations),
            "evaluations": len(p.evaluations),
            "validation_failures": len(self._issues()),
        }
        result: dict[str, int | float] = {
            f"v11_reasoning_fabric_{key}_total": value for key, value in values.items()
        }
        result["v11_reasoning_fabric_health_status"] = int(not self._issues())
        result["v11_reasoning_fabric_evaluation_seconds"] = 0.0
        result["v11_reasoning_fabric_explanation_seconds"] = 0.0
        return result

    def audit(self) -> dict[str, object]:
        return {"items": self._profile.audit_references, "append_enabled": False}

    def lifecycle(self) -> dict[str, object]:
        return {"status": self._profile.lifecycle, "mutation_enabled": False}

    def overview(self) -> dict[str, object]:
        return {
            "profile": self.profile(),
            "validation": self.validation(),
            "diagnostics": self.diagnostics(),
            "health": self.health(),
            "metrics": self.metrics(),
            "local_first": True,
            "advisory": True,
            "read_only": True,
            "deterministic": True,
            "bounded": True,
            "automatic_decision": False,
            "automatic_planning": False,
            "runtime_mutation": False,
            "configuration_mutation": False,
            "storage_mutation": False,
            "external_network_calls": False,
            "hidden_reasoning_storage": False,
            "private_scratchpad_storage": False,
        }

    @classmethod
    def serialize(cls, value: Any) -> Any:
        if is_dataclass(value) and not isinstance(value, type):
            value = {item.name: getattr(value, item.name) for item in fields(value)}
        if isinstance(value, Mapping):
            filtered = filter_secrets(value)
            assert isinstance(filtered, dict)
            return {str(key): cls.serialize(item) for key, item in filtered.items()}
        if isinstance(value, (tuple, list, set, frozenset)):
            items: Iterable[object] = value
            return [cls.serialize(item) for item in items]
        if isinstance(value, Enum):
            return value.value
        return value

    def projection(self, value: object) -> object:
        return self.serialize(value)


__all__ = (
    "Alternative",
    "Assumption",
    "AutonomousReasoningFabric",
    "Claim",
    "ClaimType",
    "Confidence",
    "Constraint",
    "Contradiction",
    "ContradictionType",
    "EVIDENCE_PROVIDERS",
    "Evaluation",
    "EvidenceReference",
    "FabricLimits",
    "InferenceReference",
    "InferenceType",
    "Premise",
    "ReasoningContext",
    "ReasoningFabricProfile",
    "SafeExplanation",
    "Uncertainty",
    "UncertaintyStatus",
)
