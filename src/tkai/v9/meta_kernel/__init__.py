"""Advisory coordination facade for the V9 Adaptive Meta-Kernel."""

from __future__ import annotations

from dataclasses import fields, is_dataclass, replace
from datetime import datetime, timezone
from typing import Any

from tkai.v9.compatibility import negotiate_generations, negotiate_version
from tkai.v9.contracts import (
    AdaptationProfile,
    ChangePlan,
    Context,
    HealthStatus,
    Lifecycle,
    MetaKernelModel,
    Reference,
)
from tkai.v9.registry import RegistryCatalog
from tkai.v9.security import filter_secrets, validate_context
from tkai.v9.topology import MetadataTopology

V8_FRAMEWORKS = (
    "hyper-kernel",
    "hyper-coordination",
    "hyper-intelligence",
    "hyper-governance",
    "hyper-knowledge",
    "hyper-reasoning",
    "hyper-decision",
    "hyper-planning",
    "hyper-simulation",
    "hyper-operations",
    "hyper-recovery",
)
V7_FRAMEWORKS = (
    "foundation",
    "capabilities",
    "service-mesh",
    "event-fabric",
    "state",
    "workflow",
    "resource",
    "security",
    "observability",
    "configuration",
    "extension",
    "ai",
    "data",
    "intelligence",
    "runtime-governance",
)
METRIC_NAMES = (
    "frameworks_total",
    "capabilities_total",
    "services_total",
    "modules_total",
    "extensions_total",
    "topology_nodes_total",
    "topology_edges_total",
    "dependency_issues_total",
    "compatibility_issues_total",
    "adaptations_total",
    "change_plans_total",
    "validation_failures_total",
    "health_status",
    "assessment_seconds",
    "compatibility_seconds",
)


class AdaptiveMetaKernel:
    """Metadata-only kernel with no execution or runtime mutation capability."""

    ID, NAME, VERSION = (
        "tkai-v9-adaptive-meta-kernel",
        "TKAI V9 Adaptive Meta-Kernel",
        "9.0.0",
    )

    def __init__(
        self, *, per_registry_limit: int = 1_000, register_defaults: bool = True
    ) -> None:
        self.registries = RegistryCatalog(per_registry_limit=per_registry_limit)
        self.topology = MetadataTopology()
        self._audit: list[dict[str, object]] = []
        self._events: list[dict[str, object]] = []
        self.model = MetaKernelModel(
            registry_references={
                name: f"v9:registry:{name}" for name in self.registries.NAMES
            },
            lifecycle=Lifecycle.REGISTERED,
        )
        if register_defaults:
            self._register_defaults()

    def _register_defaults(self) -> None:
        for version, names in (("8.0.0", V8_FRAMEWORKS), ("7.0.0", V7_FRAMEWORKS)):
            generation = version.split(".")[0]
            for name in names:
                record = Reference(
                    f"v{generation}-{name}",
                    version,
                    "framework",
                    health=HealthStatus.UNKNOWN,
                )
                self.register("frameworks", record, actor="bootstrap")
                self.topology.add_node(record)
        self.register(
            "frameworks",
            Reference("v6-tiktok-ai-centers", "6.0.0", "framework"),
            actor="bootstrap",
        )
        for source, target in (("v6", "v7"), ("v7", "v8"), ("v8", "v9"), ("v6", "v9")):
            self.register(
                "compatibility",
                Reference(f"{source}-to-{target}", "1.0.0", "compatibility"),
                actor="bootstrap",
            )
        for name in (
            "v8-hyper-governance",
            "v7-runtime-governance",
            "v7-security",
            "v7-configuration",
            "v6-autonomous-governance",
            "v6-risk-control",
        ):
            self.register(
                "policies",
                Reference(name, "1.0.0", "read-only-policy-source"),
                actor="bootstrap",
            )

    @property
    def framework_registry(self):  # type: ignore[no-untyped-def]
        return self.registries.frameworks

    @property
    def capability_registry(self):  # type: ignore[no-untyped-def]
        return self.registries.capabilities

    def register(
        self, registry: str, record: Reference, *, actor: str = "system"
    ) -> Reference:
        result = self.registries.get(registry).register(record)
        self._record("registered", registry, record.identifier, actor)
        return result

    def _record(self, action: str, subject: str, reference: str, actor: str) -> None:
        entry: dict[str, object] = {
            "action": action,
            "subject": subject,
            "reference": reference,
            "actor": actor,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._audit.append(entry)
        self._events.append({"event": action.replace("-", "_"), **entry})

    def add_context(self, context: Context, *, actor: str = "system") -> Context:
        validate_context(context)
        self.register(
            "contexts",
            Reference(context.context_id, context.version, "context", context.scope),
            actor=actor,
        )
        return context

    def assess(
        self,
        profile: AdaptationProfile,
        *,
        paused: bool = False,
        maintenance: bool = False,
        kill_switch: bool = False,
    ) -> dict[str, object]:
        blocked = tuple(
            name
            for name, enabled in (
                ("paused", paused),
                ("maintenance", maintenance),
                ("kill-switch", kill_switch),
            )
            if enabled
        )
        self.register(
            "adaptations",
            Reference(profile.adaptation_id, profile.version, "advisory-adaptation"),
            actor="assessment",
        )
        return {
            "profile": self.serialize(profile),
            "eligible": not blocked,
            "blocked_by": blocked,
            "execution": "disabled",
        }

    def plan(self, change_plan: ChangePlan) -> dict[str, object]:
        self.register(
            "change_plans",
            Reference(
                change_plan.change_plan_id, change_plan.version, "advisory-change-plan"
            ),
            actor="planner",
        )
        return {
            "plan": self.serialize(change_plan),
            "application": "disabled",
            "runtime_mutation": False,
        }

    def negotiate(self, source: str, target: str) -> dict[str, object]:
        return dict(negotiate_generations(source, target))

    def version_negotiation(
        self, requested: str = "9.0.0", available: tuple[str, ...] = ("9.0.0",)
    ) -> dict[str, object]:
        result = self.serialize(negotiate_version(requested, available))
        assert isinstance(result, dict)
        return result

    def validation(self) -> dict[str, object]:
        issues = self.topology.issues()
        return {
            "valid": not issues,
            "issues": issues,
            "reference_integrity": not issues,
            "metadata_integrity": True,
            "bounded": True,
            "execution": "disabled",
        }

    def diagnostics(self) -> tuple[dict[str, object], ...]:
        return tuple(
            {"source": "dependency", **issue} for issue in self.topology.issues()
        )

    def health(self) -> dict[str, object]:
        issues = self.topology.issues()
        return {
            "status": "degraded" if issues else "healthy",
            "readiness": not issues,
            "liveness": True,
            "diagnostics": len(issues),
        }

    def metrics(self) -> dict[str, object]:
        counts = {
            "frameworks_total": len(self.registries.frameworks),
            "capabilities_total": len(self.registries.capabilities),
            "services_total": len(self.registries.services),
            "modules_total": len(self.registries.modules),
            "extensions_total": len(self.registries.extensions),
            "topology_nodes_total": len(self.topology.nodes()),
            "topology_edges_total": len(self.topology.edges()),
            "dependency_issues_total": len(self.topology.issues()),
            "compatibility_issues_total": 0,
            "adaptations_total": len(self.registries.adaptations),
            "change_plans_total": len(self.registries.change_plans),
            "validation_failures_total": int(bool(self.topology.issues())),
            "health_status": int(not self.topology.issues()),
            "assessment_seconds": 0.0,
            "compatibility_seconds": 0.0,
        }
        return {f"v9_meta_kernel_{name}": counts[name] for name in METRIC_NAMES}

    def lifecycle(self) -> dict[str, object]:
        return {
            "current": self.model.lifecycle.value,
            "states": tuple(state.value for state in Lifecycle),
            "planning_reference_executes": False,
            "approved_reference_executes": False,
        }

    def set_lifecycle_reference(
        self, lifecycle: Lifecycle, *, actor: str = "system"
    ) -> None:
        self.model = replace(
            self.model, lifecycle=lifecycle, updated_at=datetime.now(timezone.utc)
        )
        self._record("lifecycle-changed", "kernel", lifecycle.value, actor)

    def audit(self) -> tuple[dict[str, object], ...]:
        return tuple(self._audit)

    def events(self) -> tuple[dict[str, object], ...]:
        return tuple(self._events)

    def overview(self) -> dict[str, object]:
        return {
            **self.serialize(self.model),
            "execution": "disabled",
            "runtime_mutation": False,
            "network_discovery": False,
            "registries": {
                name: len(self.registries.get(name)) for name in self.registries.NAMES
            },
        }

    @staticmethod
    def serialize(value: Any) -> Any:
        if is_dataclass(value) and not isinstance(value, type):
            value = {field.name: getattr(value, field.name) for field in fields(value)}
        if isinstance(value, dict):
            filtered = filter_secrets(value)
            assert isinstance(filtered, dict)
            return {
                str(key): AdaptiveMetaKernel.serialize(item)
                for key, item in filtered.items()
            }
        if isinstance(value, (tuple, list, set, frozenset)):
            return [AdaptiveMetaKernel.serialize(item) for item in value]
        if hasattr(value, "value"):
            return value.value
        if isinstance(value, datetime):
            return value.isoformat()
        return value


__all__ = ("AdaptiveMetaKernel", "METRIC_NAMES", "V7_FRAMEWORKS", "V8_FRAMEWORKS")
