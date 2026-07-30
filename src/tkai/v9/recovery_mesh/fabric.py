"""Composition root for the advisory V9 Adaptive Recovery Mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import cast

from tkai.v8.observability import Observability
from tkai.v9.recovery_mesh.contracts import Dependency, RecoveryLifecycle
from tkai.v9.recovery_mesh.federation import ReadOnlyFederation
from tkai.v9.recovery_mesh.registry import RegistryCatalog, ScopedRecord
from tkai.v9.recovery_mesh.security import secure_metadata


def _serialize(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        result = {
            field.name: _serialize(getattr(value, field.name))
            for field in fields(value)
        }
        name = value.__class__.__name__
        if name in {
            "OperationReference",
            "Recommendation",
            "AdvisoryRecord",
            "RecoveryRecord",
            "Incident",
        }:
            result["executable"] = False
        if name == "RecoveryRecord":
            result["restores_snapshot"] = False
            result["activates_degraded_mode"] = False
        if name == "Approval":
            result["authorizes_execution"] = False
        return result
    if isinstance(value, Mapping):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_serialize(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    return value


class AdaptiveRecoveryMesh:
    ID = "tkai-v9-adaptive-operations-mesh"
    VERSION = "9.0.0"
    MODE = "advisory-read-only"

    def __init__(
        self,
        *,
        metadata: Mapping[str, object] | None = None,
        maximum_sources: int = 128,
        maximum_records: int = 1000,
    ) -> None:
        self.metadata = secure_metadata(metadata or {})
        self.registries = RegistryCatalog(maximum_records)
        self.federation = ReadOnlyFederation(maximum_sources)
        self.observability = Observability()
        self.observability.audit("recovery.initialized", "system", self.ID)

    def federate(
        self, sources: tuple[object, ...], actor: str = "system"
    ) -> tuple[object, ...]:
        references = self.federation.federate(sources)  # type: ignore[arg-type]
        self.observability.increment("recovery.sources.federated", len(references))
        self.observability.audit(
            "recovery.sources.federated",
            actor,
            self.ID,
            {"references": len(references)},
        )
        return references

    def register(self, resource: str, value: object, actor: str = "system") -> object:
        registry = dict(self.registries.named()).get(resource)
        if registry is None:
            raise ValueError(f"unknown recovery resource: {resource}")
        registered = registry.register(cast(ScopedRecord, value))
        self.observability.increment(f"recovery.{resource}.registered")
        self.observability.audit(f"recovery.{resource}.registered", actor, resource)
        return registered

    def dependency_issues(self) -> tuple[dict[str, object], ...]:
        dependencies = cast(
            tuple[Dependency, ...], self.registries.dependencies.discover()
        )
        known = {item.subject_reference.identifier for item in dependencies}
        graph = {
            item.subject_reference.identifier: {
                ref.identifier for ref in item.required_references
            }
            for item in dependencies
        }
        issues: list[dict[str, object]] = []
        for item in dependencies:
            for required in item.required_references:
                if required.identifier not in known:
                    issues.append(
                        {
                            "type": "missing_dependency",
                            "dependency_id": item.dependency_id,
                            "reference": required.identifier,
                        }
                    )
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                issues.append({"type": "circular_dependency", "reference": node})
                return
            if node in visited:
                return
            visiting.add(node)
            for child in graph.get(node, set()):
                if child in graph:
                    visit(child)
            visiting.remove(node)
            visited.add(node)

        for node in graph:
            visit(node)
        return tuple(issues)

    def overview(self) -> dict[str, object]:
        return {
            "mesh_id": self.ID,
            "version": self.VERSION,
            "mode": self.MODE,
            "metadata_only": True,
            "reference_only": True,
            "advisory": True,
            "execution": "disabled",
            "runtime_mutation": "disabled",
            "workflow_start": "disabled",
            "scheduler_mutation": "disabled",
            "service_mutation": "disabled",
            "resource_allocation": "disabled",
            "reservation_mutation": "disabled",
            "recovery_execution": "disabled",
            "continuity_activation": "disabled",
            "maintenance_activation": "disabled",
            "pause_mutation": "disabled",
            "killswitch_mutation": "disabled",
            "tiktok_actions": "disabled",
            "supported_generations": ("v6", "v7", "v8", "v9"),
            "metadata": dict(self.metadata),
        }

    def governance(self) -> dict[str, object]:
        return {
            "references": (
                "v9_adaptive_governance_mesh",
                "v9_adaptive_meta_kernel",
                "v8_hyper_governance_fabric",
                "v7_runtime_governance_framework",
                "v7_security_framework",
                "v6_autonomous_governance_center",
                "v6_risk_control_center",
            ),
            "pause_aware": True,
            "maintenance_aware": True,
            "killswitch_aware": True,
            "approves_execution": False,
        }

    def compatibility(self) -> dict[str, object]:
        return {
            "generations": ("v6", "v7", "v8", "v9"),
            "reference_only": True,
            "automatic_migration": False,
        }

    def analytics(self) -> dict[str, object]:
        totals: dict[str, object] = {
            f"{name}_total": len(registry) for name, registry in self.registries.named()
        }
        totals["dependency_issues_total"] = len(self.dependency_issues())
        totals["capacity_shortfalls_total"] = sum(
            1
            for item in self.registries.capacity.discover()
            if getattr(item, "estimated_shortfall", 0) > 0
        )
        return totals

    def diagnostics(self) -> tuple[dict[str, object], ...]:
        return self.dependency_issues()

    def health(self) -> dict[str, object]:
        issues = self.dependency_issues()
        return {
            "status": "degraded" if issues else "healthy",
            "readiness": not issues,
            "liveness": True,
            "framework_readiness": not issues,
            "components": {
                name: "healthy"
                for name in (
                    "registry",
                    "federation",
                    "operations",
                    "workflows",
                    "capabilities",
                    "services",
                    "resources",
                    "runtime",
                    "readiness",
                    "capacity",
                    "dependencies",
                    "recovery",
                    "continuity",
                    "governance",
                    "compatibility",
                )
            },
            "diagnostics": issues,
        }

    def metrics(self) -> dict[str, object]:
        counts = {
            "profiles": "profiles",
            "operations": "operations",
            "workflows": "workflows",
            "capabilities": "capabilities",
            "services": "services",
            "resources": "resources",
            "runtime_references": "runtime",
            "readiness_assessments": "readiness",
            "risks": "risks",
            "recovery_references": "recovery",
            "continuity_references": "continuity",
            "recommendations": "recommendations",
            "reviews": "reviews",
            "approvals": "approvals",
        }
        result: dict[str, object] = {
            f"v9_recovery_mesh_{metric}_total": len(getattr(self.registries, registry))
            for metric, registry in counts.items()
        }
        result.update(
            {
                "v9_recovery_mesh_dependency_issues_total": len(
                    self.dependency_issues()
                ),
                "v9_recovery_mesh_capacity_shortfalls_total": self.analytics()[
                    "capacity_shortfalls_total"
                ],
                "v9_recovery_mesh_validation_failures_total": 0,
                "v9_recovery_mesh_readiness": 1 if not self.dependency_issues() else 0,
                "v9_recovery_mesh_capacity_feasibility": 1,
                "v9_recovery_mesh_quality": 1,
                "v9_recovery_mesh_assessment_seconds": 0,
                "v9_recovery_mesh_health_status": 1
                if not self.dependency_issues()
                else 0,
            }
        )
        return result

    def history(self, limit: int = 100) -> dict[str, object]:
        return {
            "immutable": True,
            "versions": [
                _serialize(item.version_metadata)
                for _, registry in self.registries.named()
                for item in registry.discover(limit=limit)
                if hasattr(item, "version_metadata")
            ],
            "audit_trail": self.observability.audit_records()[-limit:],
        }

    def snapshot(self, limit: int = 100) -> dict[str, object]:
        records = {
            name: [_serialize(item) for item in registry.discover(limit=limit)]
            for name, registry in self.registries.named()
        }
        records["governance"] = records.pop("governance_records")
        records["compatibility"] = records.pop("compatibility_records")
        return {
            "overview": self.overview(),
            **records,
            "federation": [_serialize(item) for item in self.federation.references()],
            "history": self.history(limit),
            "analytics": self.analytics(),
            "diagnostics": self.diagnostics(),
            "health": self.health(),
            "metrics": self.metrics(),
            "audit": self.observability.audit_records(),
            "lifecycle": {
                "states": tuple(item.value for item in RecoveryLifecycle),
                "authorizes_execution": False,
            },
        }

    executes_tiktok_actions = mutates_runtime_state = executes_recovery = (
        executes_rollback
    ) = restores_snapshots = restarts_services = activates_degraded_mode = (
        activates_continuity
    ) = approves_execution = staticmethod(lambda: False)


RecoveryMesh = AdaptiveRecoveryMesh
__all__ = ("AdaptiveRecoveryMesh", "RecoveryMesh")
