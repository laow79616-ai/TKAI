"""TKAI V8 execution-independent Hyper Kernel composition root."""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID, uuid5

from tkai.v8.compatibility import CompatibilityMatrix
from tkai.v8.contracts import (
    Diagnostic,
    FrameworkKind,
    HealthStatus,
    RegistryRecord,
    Scope,
)
from tkai.v8.observability import Observability
from tkai.v8.registry import MetadataRegistry, RegistryCatalog
from tkai.v8.security import AccessController, Principal, filter_secrets
from tkai.v8.services import (
    DependencyGraph,
    DiagnosticsAggregator,
    DiscoveryService,
    HealthAggregator,
)

_KERNEL_NAMESPACE = UUID("229e1e20-b57e-4f34-b33c-999927c03c8a")


class HyperKernel:
    """Unified coordination layer for framework metadata and references.

    The kernel deliberately has no execute, dispatch, publish, or TikTok action API.
    """

    VERSION = "8.0.0"
    ID = str(uuid5(_KERNEL_NAMESPACE, f"tkai-hyper-kernel:{VERSION}"))

    def __init__(
        self,
        *,
        metadata: Mapping[str, object] | None = None,
        register_defaults: bool = True,
    ) -> None:
        self.metadata = filter_secrets(metadata or {})
        self.registries = RegistryCatalog()
        self.compatibility = CompatibilityMatrix()
        self.observability = Observability()
        self.access = AccessController()
        self.discovery = DiscoveryService(self.registries)
        self._health = HealthAggregator()
        self._diagnostics = DiagnosticsAggregator()
        self._diagnostic_records: list[Diagnostic] = []
        if register_defaults:
            self._register_defaults()

    @property
    def framework_registry(self) -> MetadataRegistry:
        return self.registries.frameworks

    @property
    def capability_registry(self) -> MetadataRegistry:
        return self.registries.capabilities

    @property
    def runtime_registry(self) -> MetadataRegistry:
        return self.registries.runtime

    @property
    def module_registry(self) -> MetadataRegistry:
        return self.registries.modules

    @property
    def extension_registry(self) -> MetadataRegistry:
        return self.registries.extensions

    @property
    def compatibility_registry(self) -> MetadataRegistry:
        return self.registries.compatibility

    @property
    def diagnostics_registry(self) -> MetadataRegistry:
        return self.registries.diagnostics

    def _register_defaults(self) -> None:
        for kind in FrameworkKind:
            identifier = (
                "future-frameworks"
                if kind is FrameworkKind.FUTURE
                else f"{kind.value.replace('_', '-')}-framework"
            )
            self.registries.frameworks.register(
                RegistryRecord(
                    identifier=identifier,
                    version=self.VERSION,
                    kind=kind.value,
                    scope=Scope(framework=identifier),
                    metadata={"coordination": "reference-only"},
                    health=HealthStatus.UNKNOWN,
                )
            )
        for target in self.compatibility.list():
            self.registries.compatibility.register(
                RegistryRecord(
                    identifier=target.identifier,
                    version=",".join(target.versions),
                    kind="compatibility",
                    metadata={"mode": target.mode},
                    health=HealthStatus.HEALTHY,
                )
            )
        self.observability.audit("kernel.initialized", "system", self.ID)

    def register(
        self,
        registry: str,
        record: RegistryRecord,
        *,
        actor: str = "system",
    ) -> RegistryRecord:
        selected = getattr(self.registries, registry, None)
        if not isinstance(selected, MetadataRegistry):
            raise ValueError(f"unknown registry: {registry}")
        registered = selected.register(record)
        self.observability.increment(f"registry.{registry}.registrations")
        self.observability.audit(
            "metadata.registered", actor, record.identifier, {"registry": registry}
        )
        return registered

    def dependency_graph(self) -> dict[str, tuple[str, ...]]:
        return DependencyGraph(self.registries.values()).as_dict()

    def add_diagnostic(self, diagnostic: Diagnostic) -> None:
        self._diagnostic_records.append(diagnostic)
        self.observability.increment("diagnostics.total")

    def health(self) -> dict[str, object]:
        return self._health.aggregate(self.registries.values())

    def diagnostics(self) -> tuple[Diagnostic, ...]:
        return self._diagnostics.aggregate(
            self.registries.values(), self._diagnostic_records
        )

    def metrics(self) -> dict[str, object]:
        return {
            "kernel_id": self.ID,
            "registries": {
                registry.name: len(registry) for registry in self.registries.values()
            },
            "counters": self.observability.metrics(),
        }

    def audit(self) -> tuple[dict[str, object], ...]:
        return self.observability.audit_records()

    def overview(self) -> dict[str, object]:
        return {
            "kernel_id": self.ID,
            "kernel_version": self.VERSION,
            "mode": "metadata-driven",
            "execution": "disabled",
            "metadata": self.metadata,
            "registries": {
                registry.name: len(registry) for registry in self.registries.values()
            },
            "health": self.health(),
        }

    @staticmethod
    def serialize_record(record: RegistryRecord) -> dict[str, object]:
        return {
            "identifier": record.identifier,
            "version": record.version,
            "kind": record.kind,
            "scope": {
                "tenant": record.scope.tenant,
                "workspace": record.scope.workspace,
                "framework": record.scope.framework,
            },
            "dependencies": [
                {"target": item.target, "optional": item.optional}
                for item in record.dependencies
            ],
            "capabilities": sorted(record.capabilities),
            "metadata": dict(record.metadata),
            "lifecycle": record.lifecycle,
            "health": record.health.value,
        }

    @staticmethod
    def serialize_diagnostic(diagnostic: Diagnostic) -> dict[str, object]:
        return {
            "code": diagnostic.code,
            "message": diagnostic.message,
            "severity": diagnostic.severity,
            "source": diagnostic.source,
            "scope": {
                "tenant": diagnostic.scope.tenant,
                "workspace": diagnostic.scope.workspace,
                "framework": diagnostic.scope.framework,
            },
            "metadata": dict(diagnostic.metadata),
        }

    def authorize_read(self, principal: Principal, scope: Scope | None = None) -> None:
        self.access.authorize(principal, "kernel:read", scope or Scope())


Kernel = HyperKernel

__all__ = ("HyperKernel", "Kernel")
