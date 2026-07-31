"""Deterministic advisory facade for the V11 intelligence-reference model."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any

from tkai.v11.compatibility import compatibility_projection
from tkai.v11.contracts import AutonomousCoreModel, IntelligenceProfile, Scope
from tkai.v11.security import (
    authorize_scope,
    filter_secrets,
    security_projection,
    validate_safe_metadata,
)

REFERENCE_RESOURCES = (
    "knowledge",
    "reasoning",
    "decision",
    "planning",
    "operations",
    "recovery",
    "governance",
    "trust",
    "integrity",
)


class AutonomousIntelligenceCore:
    """Pure projection service with no action or mutation methods."""

    def __init__(
        self,
        model: AutonomousCoreModel | None = None,
        *,
        scope: Scope | None = None,
    ) -> None:
        self._model = model or AutonomousCoreModel()
        self._scope = scope or self._model.scope
        authorize_scope(self._scope, self._model.scope)
        validate_safe_metadata(self._model.safe_metadata)
        validate_safe_metadata(self._model.intelligence_profile.safe_metadata)
        confidence = self._model.intelligence_profile.confidence
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

    @property
    def model(self) -> AutonomousCoreModel:
        return self._model

    def core(self) -> dict[str, object]:
        result = self.serialize(self._model)
        assert isinstance(result, dict)
        return {**result, "security": security_projection()}

    def profile(self) -> dict[str, object]:
        result = self.serialize(self._model.intelligence_profile)
        assert isinstance(result, dict)
        return {**result, "hidden_reasoning": False, "execution": "disabled"}

    def contexts(self) -> dict[str, object]:
        return {
            "context": self.profile()["context"],
            "scope": self.serialize(self._scope),
            "read_only": True,
        }

    def references(self, resource: str) -> dict[str, object]:
        if resource not in REFERENCE_RESOURCES:
            raise KeyError(resource)
        values = getattr(self._model, f"{resource}_references")
        return {
            "resource": resource,
            "references": values,
            "source_version": "v10",
            "read_only": True,
            "executable": False,
        }

    def compatibility(self) -> dict[str, object]:
        return compatibility_projection()

    def validation(self) -> dict[str, object]:
        return {
            "valid": True,
            "issues": (),
            "metadata_only": True,
            "deterministic": True,
            "read_only": True,
            "execution": "disabled",
        }

    def diagnostics(self) -> dict[str, object]:
        return {"items": (), "status": "clear", "read_only": True}

    def health(self) -> dict[str, object]:
        return {
            "status": self._model.health,
            "readiness": True,
            "liveness": True,
            "execution_readiness": False,
        }

    def metrics(self) -> dict[str, int | float]:
        return {
            "v11_intelligence_reference_domains_total": len(REFERENCE_RESOURCES),
            "v11_intelligence_compatibility_generations_total": 6,
            "v11_intelligence_validation_failures_total": 0,
            "v11_intelligence_health_status": 1,
            **self._model.metrics,
        }

    def audit(self) -> dict[str, object]:
        return {"items": self.serialize(self._model.audit), "append_enabled": False}

    def overview(self) -> dict[str, object]:
        return {
            "core_id": self._model.core_id,
            "version": self._model.version,
            "profile": self.profile(),
            "references": {
                resource: self.references(resource)["references"]
                for resource in REFERENCE_RESOURCES
            },
            "compatibility": self.compatibility(),
            "health": self.health(),
            "metrics": self.metrics(),
            "security": security_projection(),
            "advisory": True,
            "deterministic": True,
            "read_only": True,
            "external_network_calls": False,
        }

    @staticmethod
    def serialize(value: Any) -> Any:
        if is_dataclass(value) and not isinstance(value, type):
            value = {item.name: getattr(value, item.name) for item in fields(value)}
        if isinstance(value, dict):
            filtered = filter_secrets(value)
            assert isinstance(filtered, dict)
            return {
                str(key): AutonomousIntelligenceCore.serialize(item)
                for key, item in filtered.items()
            }
        if isinstance(value, (tuple, list, set, frozenset)):
            return [AutonomousIntelligenceCore.serialize(item) for item in value]
        if isinstance(value, Enum):
            return value.value
        return value


__all__ = (
    "AutonomousCoreModel",
    "AutonomousIntelligenceCore",
    "IntelligenceProfile",
    "REFERENCE_RESOURCES",
    "Scope",
)
