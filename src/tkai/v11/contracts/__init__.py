"""Immutable contracts for the TKAI V11 Autonomous Intelligence Core."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


def _empty_mapping() -> Mapping[str, object]:
    return MappingProxyType({})


def _empty_metrics() -> Mapping[str, int | float]:
    return MappingProxyType({})


@dataclass(frozen=True)
class Scope:
    """Tenant and workspace boundary inherited by every V11 projection."""

    tenant: str = "local"
    workspace: str = "default"
    namespace: str = "tkai.v11"


@dataclass(frozen=True)
class IntelligenceProfile:
    """Advisory intelligence metadata; deliberately contains no reasoning trace."""

    profile_id: str = "tkai-v11-default-intelligence-profile"
    context: Mapping[str, object] = field(default_factory=_empty_mapping)
    objectives: tuple[str, ...] = ()
    constraints: tuple[str, ...] = (
        "advisory-only",
        "deterministic",
        "read-only",
        "local-first",
    )
    evidence_references: tuple[str, ...] = ()
    confidence: float = 0.0
    limitations: tuple[str, ...] = ("metadata-reference-only",)
    compatibility_references: tuple[str, ...] = ()
    governance_references: tuple[str, ...] = ()
    trust_references: tuple[str, ...] = ()
    integrity_references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)
    safe_metadata: Mapping[str, object] = field(default_factory=_empty_mapping)
    executable: bool = field(default=False, init=False)


@dataclass(frozen=True)
class AutonomousCoreModel:
    """Unified, immutable intelligence-reference model."""

    core_id: str = "tkai-v11-autonomous-intelligence-core"
    version: str = "11.0.0"
    intelligence_profile: IntelligenceProfile = field(
        default_factory=IntelligenceProfile
    )
    knowledge_references: tuple[str, ...] = ("v10:knowledge-mesh",)
    reasoning_references: tuple[str, ...] = ("v10:reasoning-mesh",)
    decision_references: tuple[str, ...] = ("v10:decision-mesh",)
    planning_references: tuple[str, ...] = ("v10:planning-mesh",)
    operations_references: tuple[str, ...] = ("v10:operations-mesh",)
    recovery_references: tuple[str, ...] = ("v10:recovery-mesh",)
    governance_references: tuple[str, ...] = ("v10:governance-mesh",)
    trust_references: tuple[str, ...] = ("v10:trust-mesh",)
    integrity_references: tuple[str, ...] = ("v10:integrity-mesh",)
    compatibility_references: tuple[str, ...] = ("v10:compatibility-mesh",)
    validation_references: tuple[str, ...] = ("v11:validation",)
    diagnostics_references: tuple[str, ...] = ("v11:diagnostics",)
    health: str = "healthy"
    metrics: Mapping[str, int | float] = field(default_factory=_empty_metrics)
    audit: tuple[Mapping[str, object], ...] = ()
    safe_metadata: Mapping[str, object] = field(default_factory=_empty_mapping)
    scope: Scope = field(default_factory=Scope)
    advisory: bool = field(default=True, init=False)
    deterministic: bool = field(default=True, init=False)
    read_only: bool = field(default=True, init=False)
    executable: bool = field(default=False, init=False)


__all__ = ("AutonomousCoreModel", "IntelligenceProfile", "Scope")
