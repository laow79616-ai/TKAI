"""Advisory facade for the TKAI V10 Sovereign Core."""

from __future__ import annotations

from dataclasses import fields, is_dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any

from tkai.v10.compatibility import negotiate
from tkai.v10.contracts import (
    ChangePlan,
    Context,
    Lifecycle,
    Reference,
    SovereignCoreModel,
    TrustDomain,
)
from tkai.v10.metrics import METRICS
from tkai.v10.registries import RegistryCatalog
from tkai.v10.security import filter_secrets, validate_safe_metadata
from tkai.v10.topology import MetadataTopology

POLICY_SOURCES = (
    "v9-adaptive-governance-mesh",
    "v9-adaptive-meta-kernel",
    "v8-hyper-governance-fabric",
    "v7-runtime-governance-framework",
    "v7-security-framework",
    "v6-autonomous-governance-center",
    "v6-risk-control-center",
)


class SovereignCore:
    """Local metadata coordination only; never executes or mutates runtime state."""

    def __init__(self, *, per_registry_limit: int = 1_000) -> None:
        self.registries = RegistryCatalog(per_registry_limit=per_registry_limit)
        refs = MappingProxyType(
            {name: f"v10:registry:{name}" for name in self.registries.NAMES}
        )
        self.model = SovereignCoreModel(registry_references=refs)
        self.topology = MetadataTopology()
        self._contexts: list[Context] = []
        self._audit: list[dict[str, object]] = []
        self._events: list[dict[str, object]] = []
        self.register("trust_domains", TrustDomain("local", "Local Trust Domain"))
        for source in POLICY_SOURCES:
            self.register(
                "policies", Reference(source, "reference", "read-only-policy-source")
            )

    def _record(self, action: str, subject: str) -> None:
        entry: dict[str, object] = {
            "action": action,
            "subject": subject,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._audit.append(entry)
        self._events.append({"event": action.replace("-", "_"), **entry})

    def register(self, registry: str, record: object) -> object:
        result = self.registries.get(registry).register(record)
        self._record("registered", registry)
        return result

    def discover(self, registry: str, *, limit: int = 100) -> tuple[object, ...]:
        return self.registries.get(registry).discover(limit=limit)

    def add_context(self, context: Context) -> Context:
        validate_safe_metadata(context.safe_metadata)
        if context.time_range and context.time_range[1] - context.time_range[
            0
        ] > timedelta(days=366):
            raise ValueError("bounded time range exceeded")
        if len(self._contexts) >= 1_000:
            raise ValueError("bounded context count exceeded")
        self._contexts.append(context)
        self._record("context-registered", context.context_id)
        return context

    def evaluate_policy(
        self,
        *,
        paused: bool = False,
        maintenance: bool = False,
        kill_switch: bool = False,
    ) -> dict[str, object]:
        blocked = tuple(
            name
            for name, active in (
                ("pause", paused),
                ("maintenance", maintenance),
                ("kill-switch", kill_switch),
            )
            if active
        )
        return {
            "eligible": not blocked,
            "blocked_by": blocked,
            "policy_execution": False,
            "advisory": True,
            "review_required": True,
            "approval_required": True,
            "audit_required": True,
        }

    def negotiate(self, source: str, *, kind: str = "framework") -> dict[str, object]:
        result = negotiate(source, kind=kind)
        self._record("compatibility-negotiated", f"{source}:{kind}")
        return result

    def plan(self, plan: ChangePlan) -> dict[str, object]:
        if not 0.0 <= plan.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        self.register("change_plans", plan)
        return {
            "plan": self.serialize(plan),
            "application": "disabled",
            "runtime_mutation": False,
            "automatic_approval": False,
        }

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

    def metrics(self) -> dict[str, int | float]:
        values: dict[str, int | float] = {name: 0 for name in METRICS}
        mapping = {
            "trust_domains": "trust_domains_total",
            "principals": "principals_total",
            "integrity": "integrity_records_total",
            "attestations": "attestations_total",
            "boundaries": "boundaries_total",
            "frameworks": "frameworks_total",
            "capabilities": "capabilities_total",
            "services": "services_total",
            "modules": "modules_total",
            "extensions": "extensions_total",
            "change_plans": "change_plans_total",
        }
        for registry, suffix in mapping.items():
            values[f"v10_sovereign_core_{suffix}"] = len(self.registries.get(registry))
        values["v10_sovereign_core_topology_nodes_total"] = len(self.topology.nodes())
        values["v10_sovereign_core_topology_edges_total"] = len(self.topology.edges())
        values["v10_sovereign_core_dependency_issues_total"] = len(
            self.topology.issues()
        )
        values["v10_sovereign_core_validation_failures_total"] = int(
            bool(self.topology.issues())
        )
        values["v10_sovereign_core_health_status"] = int(not self.topology.issues())
        return values

    def lifecycle(self) -> dict[str, object]:
        return {
            "current": self.model.lifecycle.value,
            "states": tuple(state.value for state in Lifecycle),
            "reference_states_execute": False,
        }

    def set_lifecycle_reference(self, lifecycle: Lifecycle) -> None:
        self.model = replace(
            self.model, lifecycle=lifecycle, updated_at=datetime.now(timezone.utc)
        )
        self._record("lifecycle-changed", lifecycle.value)

    def audit(self) -> tuple[dict[str, object], ...]:
        return tuple(self._audit)

    def events(self) -> tuple[dict[str, object], ...]:
        return tuple(self._events)

    def overview(self) -> dict[str, object]:
        result = self.serialize(self.model)
        assert isinstance(result, dict)
        return {
            **result,
            "execution": "disabled",
            "runtime_mutation": False,
            "remote_control_plane": False,
            "external_network_calls": False,
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
                str(key): SovereignCore.serialize(item)
                for key, item in filtered.items()
            }
        if isinstance(value, (tuple, list, set, frozenset)):
            return [SovereignCore.serialize(item) for item in value]
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, datetime):
            return value.isoformat()
        return value


__all__ = ("POLICY_SOURCES", "SovereignCore")
