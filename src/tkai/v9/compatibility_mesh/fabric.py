"""Composition root for the advisory V9 Adaptive Compatibility Mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import cast

from tkai.v8.observability import Observability
from tkai.v9.compatibility_mesh.contracts import CompatibilityLifecycle
from tkai.v9.compatibility_mesh.federation import ReadOnlyFederation
from tkai.v9.compatibility_mesh.registry import RegistryCatalog, ScopedRecord
from tkai.v9.compatibility_mesh.security import secure_metadata


def _serialize(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        result = {
            field.name: _serialize(getattr(value, field.name))
            for field in fields(value)
        }
        name = value.__class__.__name__
        if name in {"CompatibilityRecord", "Recommendation"}:
            result.update({"advisory": True, "executable": False})
        if name == "CompatibilityRecord":
            result.update(
                {
                    "mutates_configuration": False,
                    "mutates_schema": False,
                    "mutates_storage": False,
                }
            )
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


class AdaptiveCompatibilityMesh:
    ID = "tkai-v9-adaptive-compatibility-mesh"
    VERSION = "9.0.0"
    MODE = "advisory-read-only"
    SUPPORTED_GENERATIONS = ("v6", "v7", "v8", "v9")

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
        self.observability.audit("compatibility.initialized", "system", self.ID)

    def federate(
        self, sources: tuple[object, ...], actor: str = "system"
    ) -> tuple[object, ...]:
        references = self.federation.federate(sources)  # type: ignore[arg-type]
        self.observability.increment("compatibility.sources.federated", len(references))
        self.observability.audit(
            "compatibility.sources.federated",
            actor,
            self.ID,
            {"references": len(references)},
        )
        return references

    def register(self, resource: str, value: object, actor: str = "system") -> object:
        registry = dict(self.registries.named()).get(resource)
        if registry is None:
            raise ValueError(f"unknown compatibility resource: {resource}")
        registered = registry.register(cast(ScopedRecord, value))
        self.observability.increment(f"compatibility.{resource}.registered")
        self.observability.audit(
            f"compatibility.{resource}.registered", actor, resource
        )
        return registered

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
            "automatic_migration": "disabled",
            "automatic_upgrade": "disabled",
            "rollback_execution": "disabled",
            "configuration_apply": "disabled",
            "schema_mutation": "disabled",
            "storage_mutation": "disabled",
            "plugin_installation": "disabled",
            "deployment_execution": "disabled",
            "tiktok_actions": "disabled",
            "supported_generations": self.SUPPORTED_GENERATIONS,
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
            "review_required": True,
            "approves_execution": False,
        }

    def compatibility(self) -> dict[str, object]:
        return {
            "generations": self.SUPPORTED_GENERATIONS,
            "v6": "backward-compatible",
            "v7": "backward-compatible",
            "v8": "backward-compatible",
            "v9": "native",
            "reference_only": True,
            "automatic_migration": False,
            "automatic_upgrade": False,
        }

    def analytics(self) -> dict[str, object]:
        totals: dict[str, object] = {
            f"{name}_total": len(registry) for name, registry in self.registries.named()
        }
        totals["incompatible_assessments_total"] = sum(
            1
            for item in self.registries.assessments.discover()
            if getattr(item, "status", "") == "incompatible"
        )
        return totals

    def diagnostics(self) -> tuple[dict[str, object], ...]:
        return tuple(
            {
                "type": "compatibility_gap",
                "assessment_id": getattr(item, "assessment_id", ""),
                "status": getattr(item, "status", ""),
            }
            for item in self.registries.assessments.discover()
            if getattr(item, "status", "") == "incompatible"
        )

    def health(self) -> dict[str, object]:
        issues = self.diagnostics()
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
                    "profiles",
                    "components",
                    "versions",
                    "capabilities",
                    "configurations",
                    "schemas",
                    "storage",
                    "plugins",
                    "deployments",
                    "assessments",
                    "matrices",
                    "compatibility",
                )
            },
            "diagnostics": issues,
        }

    def metrics(self) -> dict[str, object]:
        result: dict[str, object] = {
            f"v9_compatibility_mesh_{name}_total": len(registry)
            for name, registry in self.registries.named()
        }
        result.update(
            {
                "v9_compatibility_mesh_validation_failures_total": len(
                    self.diagnostics()
                ),
                "v9_compatibility_mesh_execution_total": 0,
                "v9_compatibility_mesh_runtime_mutations_total": 0,
                "v9_compatibility_mesh_migrations_total": 0,
                "v9_compatibility_mesh_upgrades_total": 0,
                "v9_compatibility_mesh_rollbacks_total": 0,
                "v9_compatibility_mesh_configuration_applies_total": 0,
                "v9_compatibility_mesh_schema_mutations_total": 0,
                "v9_compatibility_mesh_storage_mutations_total": 0,
                "v9_compatibility_mesh_plugin_installations_total": 0,
                "v9_compatibility_mesh_deployments_total": 0,
                "v9_compatibility_mesh_health_status": 0 if self.diagnostics() else 1,
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
                "states": tuple(item.value for item in CompatibilityLifecycle),
                "authorizes_execution": False,
            },
        }

    executes_tiktok_actions = mutates_runtime_state = executes_migration = (
        executes_upgrade
    ) = executes_rollback = applies_configuration = mutates_schema = mutates_storage = (
        installs_plugins
    ) = executes_deployment = approves_execution = staticmethod(lambda: False)


CompatibilityMesh = AdaptiveCompatibilityMesh
__all__ = ("AdaptiveCompatibilityMesh", "CompatibilityMesh")
