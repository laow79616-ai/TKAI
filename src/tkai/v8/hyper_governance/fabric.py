"""Composition root for the V8 Hyper Governance Fabric."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum

from tkai.v8.hyper_governance.contracts import (
    ApprovalRecord,
    BoundaryRecord,
    CompatibilityRecord,
    ComplianceRecord,
    ConstraintRecord,
    GovernanceProfile,
    GovernanceReference,
    PolicyRecord,
    ReviewRecord,
)
from tkai.v8.hyper_governance.governance import PolicyFabric
from tkai.v8.hyper_governance.registry import GovernanceRegistryCatalog
from tkai.v8.hyper_governance.relationships import (
    GovernanceRelationship,
    RelationshipGraph,
)
from tkai.v8.hyper_governance.security import secure_metadata
from tkai.v8.observability import Observability


def _serialize(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _serialize(getattr(value, item.name)) for item in fields(value)
        }
    if isinstance(value, Mapping):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_serialize(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    return value


def serialize_record(value: object) -> dict[str, object]:
    serialized = _serialize(value)
    if not isinstance(serialized, dict):
        raise TypeError("governance records must serialize to mappings")
    if isinstance(value, (GovernanceProfile, ApprovalRecord)):
        serialized["execution_authorized"] = False
    if isinstance(value, PolicyRecord):
        serialized["enforced"] = False
    return serialized


class HyperGovernanceFabric:
    """Unified, advisory governance metadata spanning V6, V7, and V8."""

    ID = "tkai-v8-hyper-governance"
    VERSION = "8.0.0"
    MODE = "reference-only"

    def __init__(self, *, metadata: Mapping[str, object] | None = None) -> None:
        self.metadata = secure_metadata(metadata or {})
        self.registries = GovernanceRegistryCatalog()
        self.policy_fabric = PolicyFabric()
        self.relationships = RelationshipGraph()
        self.observability = Observability()
        self._sources: dict[str, tuple[GovernanceReference, ...]] = {
            source: () for source in PolicyFabric.SOURCE_NAMES
        }
        self.observability.audit("governance.initialized", "system", self.ID)

    def aggregate_metadata(
        self,
        *,
        v6_governance: tuple[GovernanceReference | Mapping[str, object], ...] = (),
        v7_frameworks: tuple[GovernanceReference | Mapping[str, object], ...] = (),
        v8_frameworks: tuple[GovernanceReference | Mapping[str, object], ...] = (),
        actor: str = "system",
    ) -> dict[str, tuple[GovernanceReference, ...]]:
        """Replace only the local reference projection."""

        self._sources = self.policy_fabric.aggregate(
            v6_governance=v6_governance,
            v7_frameworks=v7_frameworks,
            v8_frameworks=v8_frameworks,
        )
        count = sum(len(items) for items in self._sources.values())
        self.observability.increment("governance.references.aggregated", count)
        self.observability.audit(
            "governance.metadata.aggregated",
            actor,
            self.ID,
            {"references": count},
        )
        return dict(self._sources)

    def _register(
        self, registry_name: str, value: object, identifier: str, actor: str
    ) -> object:
        registry = getattr(self.registries, registry_name)
        registered = registry.register(value)
        self.observability.increment(f"governance.{registry_name}.registered")
        self.observability.audit(
            f"governance.{registry_name}.registered", actor, identifier
        )
        return registered

    def register_profile(
        self, value: GovernanceProfile, actor: str = "system"
    ) -> GovernanceProfile:
        return self._register("profiles", value, value.profile_id, actor)  # type: ignore[return-value]

    def register_policy(
        self, value: PolicyRecord, actor: str = "system"
    ) -> PolicyRecord:
        return self._register("policies", value, value.policy_id, actor)  # type: ignore[return-value]

    def register_constraint(
        self, value: ConstraintRecord, actor: str = "system"
    ) -> ConstraintRecord:
        return self._register(  # type: ignore[return-value]
            "constraints", value, value.constraint_id, actor
        )

    def register_boundary(
        self, value: BoundaryRecord, actor: str = "system"
    ) -> BoundaryRecord:
        return self._register(  # type: ignore[return-value]
            "boundaries", value, value.boundary_id, actor
        )

    def register_compliance(
        self, value: ComplianceRecord, actor: str = "system"
    ) -> ComplianceRecord:
        return self._register(  # type: ignore[return-value]
            "compliance", value, value.compliance_id, actor
        )

    def register_review(
        self, value: ReviewRecord, actor: str = "system"
    ) -> ReviewRecord:
        return self._register("reviews", value, value.review_id, actor)  # type: ignore[return-value]

    def register_approval(
        self, value: ApprovalRecord, actor: str = "system"
    ) -> ApprovalRecord:
        return self._register(  # type: ignore[return-value]
            "approvals", value, value.approval_id, actor
        )

    def register_compatibility(
        self, value: CompatibilityRecord, actor: str = "system"
    ) -> CompatibilityRecord:
        return self._register(  # type: ignore[return-value]
            "compatibility", value, value.compatibility_id, actor
        )

    def add_relationship(
        self, value: GovernanceRelationship, actor: str = "system"
    ) -> GovernanceRelationship:
        added = self.relationships.add(value)
        self.observability.increment("governance.relationships.registered")
        self.observability.audit(
            "governance.relationship.registered",
            actor,
            f"{value.source}:{value.target}",
        )
        return added

    def diagnostics(self) -> tuple[dict[str, object], ...]:
        findings: list[dict[str, object]] = []
        for policy in self.registries.policies.discover():
            if not policy.framework_references:
                findings.append(
                    {
                        "code": "policy-without-framework",
                        "severity": "info",
                        "policy_id": policy.policy_id,
                    }
                )
        for review in self.registries.reviews.discover():
            if review.status == "pending":
                findings.append(
                    {
                        "code": "review-pending",
                        "severity": "info",
                        "review_id": review.review_id,
                    }
                )
        return tuple(findings)

    def health(self) -> dict[str, object]:
        return {
            "status": "healthy",
            "mode": self.MODE,
            "advisory": True,
            "execution": "disabled",
            "runtime_mutation": "disabled",
            "automatic_approval": "disabled",
            "sources": {
                generation: len(items) for generation, items in self._sources.items()
            },
            "diagnostics": self.diagnostics(),
        }

    def metrics(self) -> dict[str, object]:
        counts = {
            name: len(getattr(self.registries, name))
            for name in (
                "profiles",
                "policies",
                "constraints",
                "boundaries",
                "compliance",
                "reviews",
                "approvals",
                "compatibility",
            )
        }
        return {
            **counts,
            "relationships": len(self.relationships.relationships()),
            "aggregated_references": sum(
                len(items) for items in self._sources.values()
            ),
            "counters": self.observability.metrics(),
        }

    def overview(self) -> dict[str, object]:
        return {
            "fabric_id": self.ID,
            "version": self.VERSION,
            "mode": self.MODE,
            "metadata_only": True,
            "advisory": True,
            "execution": "disabled",
            "runtime_mutation": "disabled",
            "execution_approval": "disabled",
            "policy_enforcement": "disabled",
            "supported_generations": ("v6", "v7", "v8"),
            "metadata": dict(self.metadata),
            "health": self.health(),
        }

    def snapshot(self) -> dict[str, object]:
        records = {
            name: [serialize_record(item) for item in registry.discover()]
            for name, registry in (
                ("profiles", self.registries.profiles),
                ("policies", self.registries.policies),
                ("constraints", self.registries.constraints),
                ("boundaries", self.registries.boundaries),
                ("compliance", self.registries.compliance),
                ("reviews", self.registries.reviews),
                ("approvals", self.registries.approvals),
                ("compatibility", self.registries.compatibility),
            )
        }
        return {
            "overview": self.overview(),
            **records,
            "sources": {
                name: [_serialize(item) for item in items]
                for name, items in self._sources.items()
            },
            "relationships": [
                serialize_record(item) for item in self.relationships.relationships()
            ],
            "health": self.health(),
            "metrics": self.metrics(),
            "diagnostics": self.diagnostics(),
            "logs": self.observability.logs(),
            "traces": [serialize_record(item) for item in self.observability.traces()],
            "audit": self.observability.audit_records(),
        }

    @staticmethod
    def executes_tiktok_actions() -> bool:
        return False

    @staticmethod
    def mutates_runtime_state() -> bool:
        return False

    @staticmethod
    def approves_execution() -> bool:
        return False

    @staticmethod
    def enforces_compliance() -> bool:
        return False


GovernanceFabric = HyperGovernanceFabric

__all__ = ("GovernanceFabric", "HyperGovernanceFabric", "serialize_record")
