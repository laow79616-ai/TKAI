"""Composition root for the advisory V8 Hyper Autonomous Operations Fabric."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass
from enum import Enum

from tkai.v8.hyper_operations import contracts
from tkai.v8.hyper_operations.registry import OperationsRegistryCatalog
from tkai.v8.hyper_operations.security import secure_metadata
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
        raise TypeError("operations records must serialize to mappings")
    result.update({"advisory": True, "read_only": True, "execution_authorized": False})
    if isinstance(value, contracts.CapacityMetadata):
        result["allocated"] = False
    if isinstance(value, contracts.RecoveryMetadata):
        result["rollback_executed"] = False
    return result


class BoundedOperationsAdapter:
    def __init__(self, source_id: str, maximum_records: int = 500) -> None:
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


class HyperOperationsFabric:
    ID = "tkai-v8-hyper-operations"
    VERSION = "8.0.0"
    MODE = "advisory-reference-only"
    SOURCE_ALLOWLIST = ("v6-ai-centers", "v7-frameworks", "v8-frameworks")
    REGISTRY_NAMES = tuple(item[0] for item in OperationsRegistryCatalog.DEFINITIONS)

    def __init__(self, *, metadata: Mapping[str, object] | None = None) -> None:
        self.metadata = secure_metadata(metadata or {})
        self.registries = OperationsRegistryCatalog()
        self.observability = Observability()
        self._sources: dict[str, tuple[Mapping[str, object], ...]] = {}
        self.observability.audit("operations.initialized", "system", self.ID)

    def aggregate_metadata(
        self,
        source_id: str,
        records: Sequence[Mapping[str, object]],
        actor: str = "system",
    ) -> tuple[Mapping[str, object], ...]:
        if source_id not in self.SOURCE_ALLOWLIST:
            raise PermissionError("source is not allowlisted")
        values = BoundedOperationsAdapter(source_id).read(records)
        self._sources[source_id] = values
        self.observability.increment("operations.references.aggregated", len(values))
        self.observability.audit(
            "operations.metadata.aggregated",
            actor,
            source_id,
            {"references": len(values)},
        )
        return values

    def _register(self, name: str, value: object, actor: str) -> object:
        if not is_dataclass(value) or isinstance(value, type):
            raise TypeError("operations record must be a dataclass instance")
        registry = getattr(self.registries, name)
        result = registry.register(value)
        identifier = next(
            str(getattr(value, item.name))
            for item in fields(value)
            if item.name.endswith("_id")
        )
        self.observability.increment(f"v8_operations_{name}_total")
        self.observability.audit(f"operations.{name}.registered", actor, identifier)
        return result

    def __getattr__(self, name: str) -> object:
        if name.startswith("register_"):
            requested = name.removeprefix("register_")
            registry_name = {
                "profile": "profiles",
                "readiness": "readiness",
                "operation": "operations",
                "workflow": "workflows",
                "runtime": "runtime",
                "resource": "resources",
                "summary": "summaries",
                "dependency": "dependencies",
                "capacity": "capacity",
                "recovery": "recovery",
                "compatibility": "compatibility",
                "health_record": "health_records",
                "metric": "metric_records",
            }.get(requested, requested)
            if registry_name in self.REGISTRY_NAMES:
                return lambda value, actor="system": self._register(
                    registry_name, value, actor
                )
        raise AttributeError(name)

    def diagnostics(self) -> tuple[dict[str, object], ...]:
        result: list[dict[str, object]] = []
        for item in self.registries.dependencies.discover():
            if item.required and not item.available:
                result.append(
                    {
                        "code": "required-dependency-unavailable",
                        "dependency_id": item.dependency_id,
                    }
                )
        return tuple(result)

    def health(self) -> dict[str, object]:
        return {
            "status": "degraded" if self.diagnostics() else "healthy",
            "mode": self.MODE,
            "advisory": True,
            "read_only": True,
            "execution": "disabled",
            "runtime_mutation": "disabled",
            "workflow_start": "disabled",
            "scheduling": "disabled",
            "browser_launch": "disabled",
            "account_start": "disabled",
            "proxy_start": "disabled",
            "device_start": "disabled",
            "resource_allocation": "disabled",
            "diagnostics": self.diagnostics(),
        }

    def metrics(self) -> dict[str, object]:
        values: dict[str, object] = {
            f"v8_operations_{name}_total": len(getattr(self.registries, name))
            for name in self.REGISTRY_NAMES
        }
        values.update(
            {
                "v8_operations_health_status": 0 if self.diagnostics() else 1,
                "v8_operations_execution_total": 0,
                "v8_operations_runtime_mutations_total": 0,
            }
        )
        return values

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
            "governance": {"advisory": True, "execution_authorized": False},
            "analytics": {
                f"{name}_total": len(getattr(self.registries, name))
                for name in self.REGISTRY_NAMES
            },
            "diagnostics": self.diagnostics(),
            "health": self.health(),
            "metrics": self.metrics(),
            "audit": self.observability.audit_records(),
            "lifecycle": [item.value for item in contracts.OperationsLifecycle],
        }

    @staticmethod
    def executes_tiktok_actions() -> bool:
        return False

    @staticmethod
    def mutates_runtime_state() -> bool:
        return False

    @staticmethod
    def starts_workflows() -> bool:
        return False

    @staticmethod
    def starts_schedules() -> bool:
        return False

    @staticmethod
    def launches_browsers() -> bool:
        return False

    @staticmethod
    def starts_accounts() -> bool:
        return False

    @staticmethod
    def starts_proxies() -> bool:
        return False

    @staticmethod
    def starts_devices() -> bool:
        return False

    @staticmethod
    def allocates_resources() -> bool:
        return False


OperationsFabric = HyperOperationsFabric
