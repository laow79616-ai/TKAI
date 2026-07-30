"""Deterministic, local-first V10 Sovereign Compatibility Mesh."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any

from tkai.v10.compatibility_mesh.contracts import (
    Assessment,
    CompatibilityPlan,
    CompatibilityProfile,
    CompatibilityRule,
    CompatibilityStatus,
    CompatibilitySubject,
    Conflict,
    ContractMetadata,
    Gap,
    InterfaceMetadata,
    Negotiation,
    RuleType,
    SchemaMetadata,
    SubjectType,
)
from tkai.v10.compatibility_mesh.registry import CompatibilityMeshRegistry
from tkai.v10.compatibility_mesh.security import filter_secrets, validate_safe_metadata

SUPPORTED_VERSIONS = ("v6", "v7", "v8", "v9", "v10")
MAX_RULES = 100
MAX_SOURCES = 100
MAX_RESULTS = 1000


class SovereignCompatibilityMesh:
    """Indexes and assesses supplied metadata without executing referenced systems."""

    def __init__(self, *, per_registry_limit: int = MAX_RESULTS) -> None:
        self.registries = CompatibilityMeshRegistry(
            per_registry_limit=per_registry_limit
        )
        self._audit: list[dict[str, object]] = []
        for version in SUPPORTED_VERSIONS:
            self.register(
                "versions", {"id": version, "version": version, "immutable": True}
            )

    def register(self, registry: str, record: object) -> object:
        metadata = getattr(record, "safe_metadata", None)
        if metadata is not None:
            validate_safe_metadata(metadata)
        result = self.registries.get(registry).register(record)
        self._audit.append(
            {"action": "metadata-registered", "subject": registry, "read_only": True}
        )
        return result

    def discover(self, registry: str, *, limit: int = 100) -> tuple[object, ...]:
        if not 0 <= limit <= MAX_RESULTS:
            raise ValueError("bounded result size exceeded")
        return self.registries.get(registry).discover(limit=limit)

    @staticmethod
    def evaluate_rule(rule: CompatibilityRule) -> CompatibilityStatus:
        if rule.rule_type is RuleType.EXACT_VERSION_MATCH:
            return (
                CompatibilityStatus.COMPATIBLE
                if rule.source_value == rule.target_value
                else CompatibilityStatus.INCOMPATIBLE
            )
        if rule.rule_type in {
            RuleType.SCHEMA_ADDITIVE_CHANGE,
            RuleType.OPTIONAL_FIELD_ADDITION,
        }:
            return CompatibilityStatus.COMPATIBLE
        if rule.rule_type in {
            RuleType.REQUIRED_FIELD_REMOVAL,
            RuleType.REQUIRED_FIELD_ADDITION,
            RuleType.TYPE_CHANGE,
            RuleType.SECURITY_CHANGE,
            RuleType.GOVERNANCE_CHANGE,
            RuleType.INTEGRITY_CHANGE,
            RuleType.TRUST_CHANGE,
        }:
            return CompatibilityStatus.REVIEW_REQUIRED
        if rule.conditions:
            return CompatibilityStatus.COMPATIBLE_WITH_CONDITIONS
        return rule.status

    def negotiate(
        self,
        negotiation_id: str,
        source_reference: str,
        target_reference: str,
        source_version: str,
        target_version: str,
        rules: tuple[CompatibilityRule, ...],
    ) -> Negotiation:
        if (
            source_version not in SUPPORTED_VERSIONS
            or target_version not in SUPPORTED_VERSIONS
        ):
            raise ValueError("unsupported TKAI version")
        if len(rules) > MAX_RULES:
            raise ValueError("bounded rule count exceeded")
        results = tuple(self.evaluate_rule(rule) for rule in rules)
        precedence = (
            CompatibilityStatus.INCOMPATIBLE,
            CompatibilityStatus.REVIEW_REQUIRED,
            CompatibilityStatus.COMPATIBLE_WITH_CONDITIONS,
        )
        status = next(
            (item for item in precedence if item in results),
            CompatibilityStatus.COMPATIBLE if results else CompatibilityStatus.UNKNOWN,
        )
        result = Negotiation(
            negotiation_id,
            source_reference,
            target_reference,
            source_version,
            target_version,
            applicable_rules=tuple(rule.rule_id for rule in rules),
            result_status=status,
            confidence=1.0 if results else 0.0,
            limitations=("metadata-only", "no migration", "no runtime mutation"),
        )
        self.register("negotiations", result)
        return result

    def health(self) -> dict[str, object]:
        conflicts = len(self.registries.get("conflicts"))
        return {
            "status": "degraded" if conflicts else "healthy",
            "liveness": True,
            "readiness": not conflicts,
            "mode": "advisory-read-only",
        }

    def metrics(self) -> dict[str, int | float]:
        values: dict[str, int | float] = {
            f"v10_compatibility_{name}_total": len(self.registries.get(name))
            for name in (
                "profiles",
                "subjects",
                "contracts",
                "interfaces",
                "schemas",
                "assessments",
                "gaps",
                "conflicts",
                "negotiations",
                "plans",
            )
        }
        for name in ("compatible", "conditional", "incompatible", "unknown"):
            values[f"v10_compatibility_{name}_total"] = 0
        values.update(
            v10_compatibility_validation_failures_total=0,
            v10_compatibility_health_status=int(self.health()["status"] == "healthy"),
            v10_compatibility_assessment_seconds=0.0,
            v10_compatibility_negotiation_seconds=0.0,
        )
        return values

    def diagnostics(self) -> dict[str, object]:
        return {
            "gaps": len(self.registries.get("gaps")),
            "conflicts": len(self.registries.get("conflicts")),
            "external_network_calls": False,
            "runtime_mutation": False,
            "migration_execution": False,
            "upgrade_execution": False,
            "rollback_execution": False,
            "automatic_approval": False,
        }

    def audit(self) -> tuple[dict[str, object], ...]:
        return tuple(self._audit)

    def overview(self) -> dict[str, object]:
        return {
            "mesh_id": "tkai-v10-sovereign-compatibility-mesh",
            "version": "10.0.0",
            "supported_versions": SUPPORTED_VERSIONS,
            "advisory": True,
            "read_only": True,
            "deterministic": True,
            "metadata_driven": True,
            "local_first": True,
            "execution": "disabled",
            "migration": False,
            "upgrade": False,
            "rollback": False,
            "runtime_mutation": False,
            "automatic_approval": False,
        }

    @staticmethod
    def serialize(value: Any) -> Any:
        if is_dataclass(value) and not isinstance(value, type):
            value = {item.name: getattr(value, item.name) for item in fields(value)}
        if isinstance(value, dict):
            filtered = filter_secrets(value)
            assert isinstance(filtered, dict)
            return {
                str(key): SovereignCompatibilityMesh.serialize(item)
                for key, item in filtered.items()
            }
        if isinstance(value, (tuple, list, set, frozenset)):
            return [SovereignCompatibilityMesh.serialize(item) for item in value]
        if isinstance(value, Enum):
            return value.value
        return value


__all__ = (
    "Assessment",
    "CompatibilityPlan",
    "CompatibilityProfile",
    "CompatibilityRule",
    "CompatibilityStatus",
    "CompatibilitySubject",
    "Conflict",
    "ContractMetadata",
    "Gap",
    "InterfaceMetadata",
    "MAX_RESULTS",
    "MAX_RULES",
    "MAX_SOURCES",
    "Negotiation",
    "RuleType",
    "SUPPORTED_VERSIONS",
    "SchemaMetadata",
    "SovereignCompatibilityMesh",
    "SubjectType",
)
