"""Local-first, advisory TKAI V10 Sovereign Knowledge Mesh."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from tkai.v10.contracts import Scope
from tkai.v10.knowledge_mesh.contracts import (
    CompatibilityRecord,
    DomainRecord,
    EvidenceRecord,
    KnowledgeConcept,
    KnowledgeDomain,
    KnowledgeEntity,
    KnowledgeProfile,
    KnowledgeRelationship,
    LineageRecord,
    ProvenanceRecord,
    RelationshipType,
)
from tkai.v10.knowledge_mesh.registry import KnowledgeMeshRegistry
from tkai.v10.knowledge_mesh.security import filter_secrets, validate_safe_metadata

SUPPORTED_GENERATIONS = ("v6", "v7", "v8", "v9", "v10")
MAX_SEARCH_RESULTS = 100


class SovereignKnowledgeMesh:
    """Indexes explicitly supplied references without ingestion or execution."""

    def __init__(self, *, per_registry_limit: int = 1_000) -> None:
        self.registries = KnowledgeMeshRegistry(per_registry_limit=per_registry_limit)
        self._audit: list[dict[str, object]] = []
        self._traces: list[dict[str, object]] = []
        self._logs: list[dict[str, object]] = []
        for generation in SUPPORTED_GENERATIONS:
            self.register(
                "compatibility",
                CompatibilityRecord(
                    f"{generation}-knowledge",
                    generation,
                    f"{generation}:completed-components",
                ),
            )

    @staticmethod
    def _safe(record: object) -> None:
        for name in ("safe_metadata", "attributes", "verification_metadata"):
            metadata = getattr(record, name, None)
            if metadata is not None:
                validate_safe_metadata(metadata)

    def register(self, registry: str, record: object) -> object:
        """Register caller-supplied metadata in local memory only."""
        self._safe(record)
        result = self.registries.get(registry).register(record)
        entry: dict[str, object] = {
            "action": "metadata-registered",
            "subject": registry,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "read_only": True,
        }
        self._audit.append(entry)
        self._traces.append({"hook": "knowledge-mesh", **entry})
        self._logs.append({"level": "info", **entry})
        return result

    def discover(
        self, registry: str, *, scope: Scope | None = None, limit: int = 100
    ) -> tuple[object, ...]:
        return self.registries.get(registry).discover(scope=scope, limit=limit)

    def search(
        self,
        query: str,
        *,
        registries: tuple[str, ...] = ("concepts", "entities", "references"),
        scope: Scope | None = None,
        limit: int = 20,
    ) -> tuple[dict[str, object], ...]:
        """Search bounded registered metadata; never scan files or networks."""
        if not query.strip():
            return ()
        if limit < 0 or limit > MAX_SEARCH_RESULTS:
            raise ValueError("search limit must be between 0 and 100")
        needle = query.casefold()
        matches: list[dict[str, object]] = []
        for registry in registries:
            for record in self.discover(registry, scope=scope, limit=500):
                serialized = self.serialize(record)
                if needle in str(serialized).casefold():
                    matches.append({"registry": registry, "record": serialized})
        return tuple(matches[:limit])

    def health(self) -> dict[str, object]:
        return {
            "status": "healthy",
            "liveness": True,
            "readiness": True,
            "mode": "advisory-read-only",
        }

    def metrics(self) -> dict[str, int]:
        values = {
            f"v10_knowledge_mesh_{name}_total": len(self.registries.get(name))
            for name in self.registries.NAMES
        }
        values["v10_knowledge_mesh_audit_entries_total"] = len(self._audit)
        return values

    def diagnostics(self) -> dict[str, object]:
        return {
            "automatic_ingestion": False,
            "production_learning": False,
            "filesystem_scanning": False,
            "external_search": False,
            "repository_mutation": False,
            "runtime_mutation": False,
            "tiktok_actions": False,
        }

    def audit(self) -> tuple[dict[str, object], ...]:
        return tuple(self._audit)

    def traces(self) -> tuple[dict[str, object], ...]:
        return tuple(self._traces)

    def structured_logs(self) -> tuple[dict[str, object], ...]:
        return tuple(self._logs)

    def overview(self) -> dict[str, object]:
        return {
            "mesh_id": "tkai-v10-sovereign-knowledge-mesh",
            "version": "10.0.0",
            "generations": SUPPORTED_GENERATIONS,
            "registries": {
                name: len(self.registries.get(name)) for name in self.registries.NAMES
            },
            "advisory": True,
            "read_only": True,
            "deterministic": True,
            "metadata_driven": True,
            "local_first": True,
            "execution": "disabled",
            "automatic_learning": False,
            "runtime_mutation": False,
        }

    @staticmethod
    def serialize(value: Any) -> Any:
        if is_dataclass(value) and not isinstance(value, type):
            value = {item.name: getattr(value, item.name) for item in fields(value)}
        if isinstance(value, dict):
            safe = filter_secrets(value)
            assert isinstance(safe, dict)
            return {
                str(key): SovereignKnowledgeMesh.serialize(item)
                for key, item in safe.items()
            }
        if isinstance(value, (tuple, list, set, frozenset)):
            return [SovereignKnowledgeMesh.serialize(item) for item in value]
        if isinstance(value, Enum):
            return value.value
        return value


__all__ = (
    "CompatibilityRecord",
    "DomainRecord",
    "EvidenceRecord",
    "KnowledgeConcept",
    "KnowledgeDomain",
    "KnowledgeEntity",
    "KnowledgeProfile",
    "KnowledgeRelationship",
    "LineageRecord",
    "MAX_SEARCH_RESULTS",
    "ProvenanceRecord",
    "RelationshipType",
    "SUPPORTED_GENERATIONS",
    "SovereignKnowledgeMesh",
)
