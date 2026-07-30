"""Composition root for the advisory V8 Hyper Recovery & Resilience Fabric."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass
from enum import Enum

from tkai.v8.hyper_recovery import contracts
from tkai.v8.hyper_recovery.registry import RecoveryRegistryCatalog
from tkai.v8.hyper_recovery.security import secure_metadata
from tkai.v8.observability import Observability


def _serialize(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _serialize(getattr(value, item.name)) for item in fields(value)
        }
    if isinstance(value, Mapping):
        return {
            str(key): _serialize(item) for key, item in secure_metadata(value).items()
        }
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    return value


def serialize_record(value: object) -> dict[str, object]:
    result = _serialize(value)
    if not isinstance(result, dict):
        raise TypeError("recovery records must serialize to mappings")
    result.update(
        advisory=True,
        read_only=True,
        execution_authorized=False,
        runtime_mutation=False,
    )
    return result


class BoundedRecoveryAdapter:
    MAXIMUM_RECORDS = 500

    def __init__(self, source_id: str, maximum_records: int = MAXIMUM_RECORDS) -> None:
        if maximum_records < 1 or maximum_records > self.MAXIMUM_RECORDS:
            raise ValueError("invalid bounded source count")
        self.source_id = source_id
        self.maximum_records = maximum_records

    def read(
        self, records: Sequence[Mapping[str, object]]
    ) -> tuple[Mapping[str, object], ...]:
        if len(records) > self.maximum_records:
            raise ValueError("bounded source count exceeded")
        return tuple(secure_metadata(item) for item in records)

    @property
    def read_only(self) -> bool:
        return True


class HyperRecoveryFabric:
    ID = "tkai-v8-hyper-recovery"
    VERSION = "8.0.0"
    MODE = "advisory-reference-only"
    SOURCE_ALLOWLIST = (
        "v8-hyper-kernel",
        "v8-hyper-coordination",
        "v8-hyper-intelligence",
        "v8-hyper-governance",
        "v8-hyper-knowledge",
        "v8-hyper-reasoning",
        "v8-hyper-decision",
        "v8-hyper-planning",
        "v8-hyper-simulation",
        "v8-hyper-operations",
        "v7-frameworks",
        "v6-recovery-resilience-center",
        "v6-risk-control-center",
        "v6-autonomous-governance-center",
        "v6-autonomous-operation-center",
        "v6-mission-engine",
        "v6-operations-planner",
        "v6-runtime-manager",
        "v6-resource-center",
        "v6-task-scheduler",
        "v6-workflow-orchestration-center",
        "v6-operations-command-center",
        "v6-performance-insights-center",
        "v6-business-intelligence-center",
        "v6-analytics-center",
    )
    REGISTRY_NAMES = tuple(item[0] for item in RecoveryRegistryCatalog.DEFINITIONS)
    LIMITS = {
        "incidents": 500,
        "steps": 250,
        "snapshots": 250,
        "checkpoints": 250,
        "results": 500,
    }

    def __init__(self, *, metadata: Mapping[str, object] | None = None) -> None:
        self.metadata = secure_metadata(metadata or {})
        self.registries = RecoveryRegistryCatalog()
        self.observability = Observability()
        self._sources: dict[str, tuple[Mapping[str, object], ...]] = {}
        self.observability.audit("recovery.initialized", "system", self.ID)

    def read_source(
        self,
        source_id: str,
        records: Sequence[Mapping[str, object]],
        actor: str = "system",
    ) -> tuple[Mapping[str, object], ...]:
        if source_id not in self.SOURCE_ALLOWLIST:
            raise PermissionError("source is not allowlisted")
        values = BoundedRecoveryAdapter(source_id).read(records)
        self._sources[source_id] = values
        self.observability.audit(
            "recovery.source.read", actor, source_id, {"references": len(values)}
        )
        return values

    aggregate_metadata = read_source

    def _register(self, name: str, value: object, actor: str) -> object:
        if not is_dataclass(value) or isinstance(value, type):
            raise TypeError("recovery record must be a dataclass instance")
        if (
            name in self.LIMITS
            and len(getattr(self.registries, name)) >= self.LIMITS[name]
        ):
            raise ValueError(f"bounded {name} count exceeded")
        result = getattr(self.registries, name).register(value)
        identifier = next(
            str(getattr(value, item.name))
            for item in fields(value)
            if item.name.endswith("_id")
        )
        self.observability.increment(f"v8_recovery_{name}_total")
        self.observability.audit(f"recovery.{name}.registered", actor, identifier)
        return result

    def __getattr__(self, name: str) -> object:
        if name.startswith("register_"):
            requested = name.removeprefix("register_")
            aliases = {
                "profile": "profiles",
                "incident": "incidents",
                "failure": "failures",
                "impact_assessment": "impact",
                "readiness_assessment": "readiness",
                "resilience_assessment": "resilience",
                "continuity_reference": "continuity",
                "recovery_plan": "plans",
                "recovery_step": "steps",
                "rollback_plan": "rollback",
                "snapshot": "snapshots",
                "checkpoint": "checkpoints",
                "restoration_plan": "restoration",
                "degraded_mode": "degraded",
                "dependency_assessment": "dependencies",
                "resource_assessment": "resources",
                "capacity_assessment": "capacity",
                "validation_result": "validation",
                "evaluation": "evaluations",
                "recommendation": "recommendations",
                "review": "reviews",
                "approval": "approvals",
                "governance_reference": "governance",
                "compatibility_reference": "compatibility",
                "version": "history",
            }
            registry_name = aliases.get(requested, requested)
            if registry_name in self.REGISTRY_NAMES:
                return lambda value, actor="system": self._register(
                    registry_name, value, actor
                )
        raise AttributeError(name)

    def validate_dependencies(
        self, dependencies: Mapping[str, Sequence[str]]
    ) -> tuple[dict[str, object], ...]:
        issues: list[dict[str, object]] = []
        names = set(dependencies)
        for source, targets in dependencies.items():
            for target in targets:
                if target not in names:
                    issues.append(
                        {
                            "code": "missing-dependency",
                            "source": source,
                            "target": target,
                        }
                    )

        visiting: set[str] = set()
        visited: set[str] = set()

        def walk(node: str, path: tuple[str, ...]) -> None:
            if node in visiting:
                issues.append({"code": "circular-dependency", "path": (*path, node)})
                return
            if node in visited:
                return
            visiting.add(node)
            for target in dependencies.get(node, ()):
                if target in names:
                    walk(target, (*path, node))
            visiting.remove(node)
            visited.add(node)

        for node in sorted(names):
            walk(node, ())
        return tuple(issues)

    @staticmethod
    def evaluate(
        evaluation_id: str,
        evaluation_type: str,
        factors: Mapping[str, float],
        weights: Mapping[str, float] | None = None,
        supporting_references: tuple[contracts.RecoveryReference, ...] = (),
        limitations: tuple[str, ...] = (),
    ) -> contracts.Evaluation:
        if not factors:
            raise ValueError("explainable evaluations require factors")
        selected = dict(weights or {name: 1.0 for name in factors})
        if set(selected) != set(factors) or any(
            weight < 0 for weight in selected.values()
        ):
            raise ValueError("weights must match factors and be non-negative")
        total = sum(selected.values())
        if total <= 0:
            raise ValueError("evaluation weight must be positive")
        if any(not 0 <= value <= 1 for value in factors.values()):
            raise ValueError("factor scores must be between zero and one")
        score = sum(factors[name] * selected[name] for name in factors) / total
        return contracts.Evaluation(
            evaluation_id=evaluation_id,
            evaluation_type=evaluation_type,
            score=score,
            factors=factors,
            weight_metadata=selected,
            supporting_references=supporting_references,
            limitations=limitations,
            explanation_summary=(
                f"{evaluation_type} weighted from {len(factors)} documented factors"
            ),
        )

    def diagnostics(self) -> tuple[dict[str, object], ...]:
        return ()

    def health(self) -> dict[str, object]:
        return {
            "status": "healthy",
            "mode": self.MODE,
            "advisory": True,
            "read_only": True,
            "execution": "disabled",
            "runtime_mutation": "disabled",
            "service_restart": "disabled",
            "workflow_start": "disabled",
            "scheduler_mutation": "disabled",
            "resource_allocation": "disabled",
            "snapshot_restoration": "disabled",
            "checkpoint_restoration": "disabled",
            "rollback_execution": "disabled",
            "degraded_mode_activation": "disabled",
            "automatic_approval": "disabled",
            "external_network": "disabled",
            "pause_aware": True,
            "kill_switch_aware": True,
            "maintenance_aware": True,
            "diagnostics": self.diagnostics(),
        }

    def metrics(self) -> dict[str, object]:
        mapping = {
            "profiles": "v8_recovery_profiles_total",
            "incidents": "v8_recovery_incidents_total",
            "failures": "v8_recovery_failures_total",
            "plans": "v8_recovery_plans_total",
            "rollback": "v8_recovery_rollbacks_total",
            "snapshots": "v8_recovery_snapshots_total",
            "checkpoints": "v8_recovery_checkpoints_total",
            "restoration": "v8_recovery_restoration_plans_total",
            "degraded": "v8_recovery_degraded_modes_total",
            "validation": "v8_recovery_validation_failures_total",
            "recommendations": "v8_recovery_recommendations_total",
            "reviews": "v8_recovery_reviews_total",
            "approvals": "v8_recovery_approvals_total",
        }
        result: dict[str, object] = {
            metric: len(getattr(self.registries, name))
            for name, metric in mapping.items()
        }
        for metric in (
            "v8_recovery_readiness",
            "v8_resilience_quality",
            "v8_continuity_quality",
            "v8_recovery_plan_quality",
            "v8_rollback_quality",
            "v8_snapshot_coverage",
            "v8_checkpoint_coverage",
            "v8_recovery_analysis_seconds",
        ):
            result[metric] = 0.0
        result["v8_recovery_health_status"] = 1
        return result

    def snapshot(self) -> dict[str, object]:
        records = {
            name: [
                serialize_record(item)
                for item in getattr(self.registries, name).discover()
            ]
            for name in self.REGISTRY_NAMES
        }
        return {
            "overview": {
                "fabric_id": self.ID,
                "version": self.VERSION,
                "mode": self.MODE,
                "advisory": True,
                "read_only": True,
                "execution_authorized": False,
                "supported_generations": ("v6", "v7", "v8"),
                "metadata": self.metadata,
            },
            **records,
            "analytics": {
                f"{name}_total": len(getattr(self.registries, name))
                for name in self.REGISTRY_NAMES
            },
            "diagnostics": self.diagnostics(),
            "health": self.health(),
            "metrics": self.metrics(),
            "audit": self.observability.audit_records(),
            "lifecycle": [item.value for item in contracts.RecoveryLifecycle],
        }

    @staticmethod
    def executes_recovery() -> bool:
        return False

    @staticmethod
    def mutates_runtime_state() -> bool:
        return False

    @staticmethod
    def restores_snapshots() -> bool:
        return False

    @staticmethod
    def restores_checkpoints() -> bool:
        return False

    @staticmethod
    def executes_rollback() -> bool:
        return False

    @staticmethod
    def activates_degraded_mode() -> bool:
        return False

    @staticmethod
    def allocates_resources() -> bool:
        return False

    @staticmethod
    def performs_tiktok_actions() -> bool:
        return False


RecoveryFabric = HyperRecoveryFabric
