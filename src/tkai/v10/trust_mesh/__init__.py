"""Advisory, read-only TKAI V10 Sovereign Trust Mesh."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from tkai.v10.contracts import Reference, Scope
from tkai.v10.trust_mesh.contracts import (
    AttestationMetadata,
    CompatibilityMetadata,
    IdentityRecord,
    IntegrityMetadata,
    PrincipalRecord,
    RelationshipStatus,
    TrustDomainKind,
    TrustDomainRecord,
    TrustMeshProfile,
    TrustRelationship,
    TrustScore,
)
from tkai.v10.trust_mesh.registry import TrustMeshRegistry
from tkai.v10.trust_mesh.security import filter_secrets, validate_safe_metadata

FEDERATED_GENERATIONS = ("v6", "v7", "v8", "v9", "v10")


class SovereignTrustMesh:
    """Federates references only; it cannot execute, mutate, or grant trust."""

    def __init__(self, *, per_registry_limit: int = 1_000) -> None:
        self.registries = TrustMeshRegistry(per_registry_limit=per_registry_limit)
        self._audit: list[dict[str, object]] = []
        self._traces: list[dict[str, object]] = []
        self._logs: list[dict[str, object]] = []
        self.register("profiles", TrustMeshProfile("tkai-v10-sovereign-trust-mesh"))
        self.register(
            "domains",
            TrustDomainRecord(
                "local-host", TrustDomainKind.LOCAL_HOST, "Local Host"
            ),
        )
        for generation in FEDERATED_GENERATIONS:
            self.register(
                "compatibility",
                CompatibilityMetadata(
                    f"{generation}-to-v10",
                    generation,
                    component_reference=f"{generation}:completed-components",
                ),
            )

    @staticmethod
    def _safe_metadata(record: object) -> None:
        metadata = getattr(record, "metadata", None)
        if metadata is not None:
            validate_safe_metadata(metadata)

    def _record(self, action: str, subject: str) -> None:
        entry: dict[str, object] = {
            "action": action,
            "subject": subject,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "read_only": True,
        }
        self._audit.append(entry)
        self._traces.append({"hook": "trust-mesh", **entry})
        self._logs.append({"level": "info", **entry})

    def register(self, registry: str, record: object) -> object:
        """Register local metadata; this never touches managed runtime state."""
        self._safe_metadata(record)
        if isinstance(record, TrustScore) and not 0.0 <= record.value <= 1.0:
            raise ValueError("trust score must be between 0 and 1")
        result = self.registries.get(registry).register(record)
        self._record("metadata-registered", registry)
        return result

    def discover(
        self, registry: str, *, scope: Scope | None = None, limit: int = 100
    ) -> tuple[object, ...]:
        """Discover isolated local metadata without assigning trust."""
        return self.registries.get(registry).discover(scope=scope, limit=limit)

    def federation(self) -> dict[str, object]:
        return {
            "generations": FEDERATED_GENERATIONS,
            "sources": {
                "v6": "trust-and-governance-modules",
                "v7": "frameworks",
                "v8": "frameworks",
                "v9": "components",
                "v10": "components",
            },
            "reference_only": True,
            "automatic_trust": False,
        }

    def health(self) -> dict[str, object]:
        return {
            "status": "healthy",
            "liveness": True,
            "readiness": True,
            "mode": "advisory-read-only",
        }

    def metrics(self) -> dict[str, int]:
        values = {
            f"v10_trust_mesh_{name}_total": len(self.registries.get(name))
            for name in self.registries.NAMES
        }
        values["v10_trust_mesh_audit_entries_total"] = len(self._audit)
        return values

    def diagnostics(self) -> dict[str, object]:
        return {
            "issues": (),
            "federated_generations": FEDERATED_GENERATIONS,
            "external_verification": False,
            "automatic_decisions": False,
            "runtime_mutation": False,
        }

    def audit(self) -> tuple[dict[str, object], ...]:
        return tuple(self._audit)

    def traces(self) -> tuple[dict[str, object], ...]:
        return tuple(self._traces)

    def structured_logs(self) -> tuple[dict[str, object], ...]:
        return tuple(self._logs)

    def overview(self) -> dict[str, object]:
        return {
            "mesh_id": "tkai-v10-sovereign-trust-mesh",
            "version": "10.0.0",
            "owner": "TKAI",
            "federation": self.federation(),
            "health": self.health(),
            "registries": {
                name: len(self.registries.get(name))
                for name in self.registries.NAMES
            },
            "advisory": True,
            "read_only": True,
            "execution": "disabled",
            "runtime_mutation": False,
            "automatic_trust": False,
            "external_network_calls": False,
        }

    @staticmethod
    def serialize(value: Any) -> Any:
        if is_dataclass(value) and not isinstance(value, type):
            value = {field.name: getattr(value, field.name) for field in fields(value)}
        if isinstance(value, dict):
            safe = filter_secrets(value)
            assert isinstance(safe, dict)
            return {
                str(key): SovereignTrustMesh.serialize(item)
                for key, item in safe.items()
            }
        if isinstance(value, (tuple, list, set, frozenset)):
            return [SovereignTrustMesh.serialize(item) for item in value]
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, datetime):
            return value.isoformat()
        return value


__all__ = (
    "AttestationMetadata",
    "CompatibilityMetadata",
    "FEDERATED_GENERATIONS",
    "IdentityRecord",
    "IntegrityMetadata",
    "PrincipalRecord",
    "Reference",
    "RelationshipStatus",
    "Scope",
    "SovereignTrustMesh",
    "TrustDomainKind",
    "TrustDomainRecord",
    "TrustMeshProfile",
    "TrustRelationship",
    "TrustScore",
)
