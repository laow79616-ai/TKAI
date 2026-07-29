"""Hyper Coordination Framework composition root."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tkai.v8.hyper_coordination.contracts import (
    CoordinationEdge,
    CoordinationLifecycle,
    CoordinationProfile,
    FrameworkDescriptor,
    GovernanceReferences,
    GraphKind,
    SynchronizationRecord,
)
from tkai.v8.hyper_coordination.dependencies import CoordinationGraph
from tkai.v8.hyper_coordination.governance import serialize_governance
from tkai.v8.hyper_coordination.registry import CoordinationRegistryCatalog
from tkai.v8.hyper_coordination.security import secure_metadata
from tkai.v8.hyper_coordination.synchronization import MetadataSynchronizer
from tkai.v8.observability import Observability


def _scope(value: Any) -> dict[str, str]:
    return {
        "tenant": value.tenant,
        "workspace": value.workspace,
        "framework": value.framework,
    }


def _reference(value: Any) -> dict[str, object]:
    return {
        "identifier": value.identifier,
        "version": value.version,
        "uri": value.uri,
        "metadata": dict(value.metadata),
    }


def serialize_profile(profile: CoordinationProfile) -> dict[str, object]:
    """Serialize a complete coordination profile."""

    return {
        "profile_id": profile.profile_id,
        "name": profile.name,
        "description": profile.description,
        "version": profile.version,
        "owner": profile.owner,
        "framework_references": [
            _reference(item) for item in profile.framework_references
        ],
        "capability_references": [
            _reference(item) for item in profile.capability_references
        ],
        "dependency_references": [
            _reference(item) for item in profile.dependency_references
        ],
        "relationship_references": [
            _reference(item) for item in profile.relationship_references
        ],
        "lifecycle": profile.lifecycle.value,
        "compatibility": [_reference(item) for item in profile.compatibility],
        "health": profile.health,
        "metrics": dict(profile.metrics),
        "audit": [dict(item) for item in profile.audit],
        "metadata": dict(profile.metadata),
        "scope": _scope(profile.scope),
        "execution_authorized": False,
    }


def serialize_framework(framework: FrameworkDescriptor) -> dict[str, object]:
    """Serialize a framework descriptor."""

    return {
        "identifier": framework.identifier,
        "version": framework.version,
        "generation": framework.generation,
        "capabilities": framework.capabilities,
        "lifecycle": framework.lifecycle.value,
        "compatibility": framework.compatibility,
        "health": framework.health,
        "scope": _scope(framework.scope),
        "metadata": dict(framework.metadata),
    }


def serialize_edge(edge: CoordinationEdge) -> dict[str, object]:
    return {
        "source": edge.source,
        "target": edge.target,
        "kind": edge.kind.value,
        "relationship": edge.relationship,
        "optional": edge.optional,
        "metadata": dict(edge.metadata),
    }


def serialize_synchronization(item: SynchronizationRecord) -> dict[str, object]:
    return {
        "synchronization_id": item.synchronization_id,
        "category": item.category,
        "source": _reference(item.source),
        "target": _reference(item.target),
        "status": item.status,
        "changes": dict(item.changes),
        "scope": _scope(item.scope),
    }


class HyperCoordinationFramework:
    """Metadata-driven advisory coordination for every TKAI framework."""

    ID = "tkai-v8-hyper-coordination"
    VERSION = "8.0.0"
    MODE = "reference-only"

    def __init__(
        self,
        *,
        metadata: Mapping[str, object] | None = None,
        register_defaults: bool = True,
    ) -> None:
        self.metadata = secure_metadata(metadata or {})
        self.registries = CoordinationRegistryCatalog()
        self.graph = CoordinationGraph()
        self.synchronizer = MetadataSynchronizer()
        self.governance = GovernanceReferences()
        self.observability = Observability()
        self._synchronizations: list[SynchronizationRecord] = []
        if register_defaults:
            self._register_defaults()
        self.observability.audit("coordination.initialized", "system", self.ID)

    def _register_defaults(self) -> None:
        defaults = (
            FrameworkDescriptor(
                "v8-hyper-kernel", "8.0.0", "v8", ("metadata-coordination",)
            ),
            FrameworkDescriptor(
                "v7-frameworks", "7.x", "v7", ("framework-coordination",)
            ),
            FrameworkDescriptor(
                "v6-ai-centers", "6.x", "v6", ("center-coordination",)
            ),
            FrameworkDescriptor(
                "future-frameworks",
                "future",
                "future",
                ("extension-coordination",),
            ),
        )
        for framework in defaults:
            self.registries.frameworks.register(framework)

    def register_profile(
        self, profile: CoordinationProfile, actor: str = "system"
    ) -> CoordinationProfile:
        registered = self.registries.profiles.register(profile)
        self.observability.increment("coordination.profiles.registered")
        self.observability.audit(
            "coordination.profile.registered", actor, profile.profile_id
        )
        return registered

    def add_edge(
        self, edge: CoordinationEdge, actor: str = "system"
    ) -> CoordinationEdge:
        added = self.graph.add(edge)
        self.observability.increment(f"coordination.graph.{edge.kind.value}.edges")
        self.observability.audit(
            "coordination.edge.added",
            actor,
            f"{edge.source}:{edge.target}",
            {"kind": edge.kind.value},
        )
        return added

    def plan_synchronization(
        self,
        category: str,
        source: Any,
        target: Any,
        changes: Mapping[str, object] | None = None,
    ) -> SynchronizationRecord:
        record = self.synchronizer.plan(category, source, target, changes)
        self._synchronizations.append(record)
        self.observability.increment("coordination.synchronizations.planned")
        return record

    def set_governance(self, references: GovernanceReferences) -> None:
        self.governance = references
        self.observability.audit(
            "coordination.governance.referenced", "system", self.ID
        )

    def health(self) -> dict[str, object]:
        cycles = {
            kind.value: len(self.graph.cycles(kind)) for kind in GraphKind
        }
        return {
            "status": "degraded" if any(cycles.values()) else "healthy",
            "frameworks": len(self.registries.frameworks),
            "profiles": len(self.registries.profiles),
            "cycles": cycles,
            "runtime_synchronization": "disabled",
            "execution": "disabled",
        }

    def metrics(self) -> dict[str, object]:
        return {
            "frameworks": len(self.registries.frameworks),
            "profiles": len(self.registries.profiles),
            "edges": len(self.graph.edges()),
            "synchronizations": len(self._synchronizations),
            "counters": self.observability.metrics(),
        }

    def diagnostics(self) -> tuple[dict[str, object], ...]:
        return tuple(
            {
                "code": "coordination-cycle",
                "severity": "warning",
                "graph": kind.value,
                "path": cycle,
            }
            for kind in GraphKind
            for cycle in self.graph.cycles(kind)
        )

    def overview(self) -> dict[str, object]:
        return {
            "framework_id": self.ID,
            "version": self.VERSION,
            "mode": self.MODE,
            "advisory": True,
            "execution": "disabled",
            "runtime_mutation": "disabled",
            "approved_reference_authorizes_execution": False,
            "metadata": dict(self.metadata),
            "lifecycle": [item.value for item in CoordinationLifecycle],
            "health": self.health(),
        }

    def snapshot(self) -> dict[str, object]:
        return {
            "overview": self.overview(),
            "profiles": [
                serialize_profile(item)
                for item in self.registries.profiles.discover()
            ],
            "frameworks": [
                serialize_framework(item)
                for item in self.registries.frameworks.discover()
            ],
            "dependencies": self.graph.snapshot(),
            "relationships": [
                serialize_edge(item)
                for item in self.graph.edges(GraphKind.RELATIONSHIP)
            ],
            "synchronization": [
                serialize_synchronization(item) for item in self._synchronizations
            ],
            "compatibility": self.graph.adjacency(GraphKind.COMPATIBILITY),
            "governance": serialize_governance(self.governance),
            "health": self.health(),
            "metrics": self.metrics(),
            "diagnostics": self.diagnostics(),
            "audit": self.observability.audit_records(),
        }


CoordinationFramework = HyperCoordinationFramework

__all__ = (
    "CoordinationFramework",
    "HyperCoordinationFramework",
    "serialize_edge",
    "serialize_framework",
    "serialize_profile",
    "serialize_synchronization",
)
