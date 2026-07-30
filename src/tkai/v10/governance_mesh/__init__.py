"""Local-first, advisory TKAI V10 Sovereign Governance Mesh."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from tkai.v10.contracts import Scope
from tkai.v10.governance_mesh.contracts import (
    ApprovalReference,
    ApprovalStatus,
    CompatibilityGovernance,
    ComplianceDomain,
    ComplianceReference,
    ConstraintReference,
    ConstraintType,
    GovernanceDomain,
    GovernanceDomainRecord,
    GovernanceProfile,
    GovernanceRelationship,
    GovernanceValidation,
    PolicyReference,
    PolicyStatus,
    RelationshipType,
    ReviewReference,
    ReviewStatus,
    RiskLevel,
    RiskReference,
    SubjectType,
    ValidationStatus,
    ValidationType,
)
from tkai.v10.governance_mesh.registry import GovernanceMeshRegistry
from tkai.v10.governance_mesh.security import filter_secrets, validate_safe_metadata

SUPPORTED_GENERATIONS = ("v6", "v7", "v8", "v9", "v10")


class SovereignGovernanceMesh:
    """Indexes governance references without executing or mutating anything."""

    def __init__(self, *, per_registry_limit: int = 1_000) -> None:
        self.registries = GovernanceMeshRegistry(per_registry_limit=per_registry_limit)
        self._audit: list[dict[str, object]] = []
        self._traces: list[dict[str, object]] = []
        self._logs: list[dict[str, object]] = []
        for generation in SUPPORTED_GENERATIONS:
            self.register(
                "compatibility",
                CompatibilityGovernance(
                    f"{generation}-governance",
                    generation,
                    f"{generation}:completed-components",
                ),
            )

    @staticmethod
    def _safe(record: object) -> None:
        metadata = getattr(record, "safe_metadata", None)
        if metadata is not None:
            validate_safe_metadata(metadata)

    def _record(self, registry: str) -> None:
        entry: dict[str, object] = {
            "action": "metadata-registered",
            "subject": registry,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "read_only": True,
        }
        self._audit.append(entry)
        self._traces.append({"hook": "governance-mesh", **entry})
        self._logs.append({"level": "info", **entry})

    def register(self, registry: str, record: object) -> object:
        """Register supplied metadata in local memory only."""
        self._safe(record)
        result = self.registries.get(registry).register(record)
        self._record(registry)
        return result

    def discover(
        self, registry: str, *, scope: Scope | None = None, limit: int = 100
    ) -> tuple[object, ...]:
        return self.registries.get(registry).discover(scope=scope, limit=limit)

    def health(self) -> dict[str, object]:
        critical_risks = sum(
            item.level is RiskLevel.CRITICAL
            for item in self.discover("risks")
            if isinstance(item, RiskReference)
        )
        invalid = sum(
            item.status is ValidationStatus.INVALID
            for item in self.discover("validation")
            if isinstance(item, GovernanceValidation)
        )
        degraded = bool(critical_risks or invalid)
        return {
            "status": "degraded" if degraded else "healthy",
            "liveness": True,
            "readiness": not degraded,
            "mode": "advisory-read-only",
        }

    def metrics(self) -> dict[str, int]:
        values = {
            f"v10_governance_mesh_{name}_total": len(self.registries.get(name))
            for name in self.registries.NAMES
        }
        values["v10_governance_mesh_audit_entries_total"] = len(self._audit)
        return values

    def diagnostics(self) -> dict[str, object]:
        return {
            "missing_approvals": self.serialize(
                tuple(
                    item
                    for item in self.discover("approvals")
                    if isinstance(item, ApprovalReference)
                    and item.status is ApprovalStatus.MISSING
                )
            ),
            "critical_risks": self.serialize(
                tuple(
                    item
                    for item in self.discover("risks")
                    if isinstance(item, RiskReference)
                    and item.level is RiskLevel.CRITICAL
                )
            ),
            "automatic_approval": False,
            "configuration_application": False,
            "runtime_mutation": False,
            "external_network_calls": False,
        }

    def audit(self) -> tuple[dict[str, object], ...]:
        return tuple(self._audit)

    def traces(self) -> tuple[dict[str, object], ...]:
        return tuple(self._traces)

    def structured_logs(self) -> tuple[dict[str, object], ...]:
        return tuple(self._logs)

    def overview(self) -> dict[str, object]:
        return {
            "mesh_id": "tkai-v10-sovereign-governance-mesh",
            "version": "10.0.0",
            "generations": SUPPORTED_GENERATIONS,
            "registries": {
                name: len(self.registries.get(name)) for name in self.registries.NAMES
            },
            "advisory": True,
            "read_only": True,
            "execution": "disabled",
            "runtime_mutation": False,
            "automatic_approval": False,
            "configuration_application": False,
            "migration": False,
            "upgrade": False,
            "rollback": False,
        }

    @staticmethod
    def serialize(value: Any) -> Any:
        if is_dataclass(value) and not isinstance(value, type):
            value = {item.name: getattr(value, item.name) for item in fields(value)}
        if isinstance(value, dict):
            filtered = filter_secrets(value)
            assert isinstance(filtered, dict)
            return {
                str(key): SovereignGovernanceMesh.serialize(item)
                for key, item in filtered.items()
            }
        if isinstance(value, (tuple, list, set, frozenset)):
            return [SovereignGovernanceMesh.serialize(item) for item in value]
        if isinstance(value, Enum):
            return value.value
        return value


__all__ = (
    "ApprovalReference",
    "ApprovalStatus",
    "CompatibilityGovernance",
    "ComplianceDomain",
    "ComplianceReference",
    "ConstraintReference",
    "ConstraintType",
    "GovernanceDomain",
    "GovernanceDomainRecord",
    "GovernanceProfile",
    "GovernanceRelationship",
    "GovernanceValidation",
    "PolicyReference",
    "PolicyStatus",
    "RelationshipType",
    "ReviewReference",
    "ReviewStatus",
    "RiskLevel",
    "RiskReference",
    "SUPPORTED_GENERATIONS",
    "SovereignGovernanceMesh",
    "SubjectType",
    "ValidationStatus",
    "ValidationType",
)
