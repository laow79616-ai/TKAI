"""Offline contracts for the V11 Autonomous Intelligence Core."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from server.api.app import create_app
from tkai.v11.api import FORBIDDEN_METHODS, GET_ROUTES, openapi_contract, route_handlers
from tkai.v11.autonomous_core import AutonomousIntelligenceCore
from tkai.v11.compatibility import SUPPORTED_GENERATIONS, V10_REFERENCES
from tkai.v11.contracts import AutonomousCoreModel, IntelligenceProfile, Scope
from tkai.v11.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v11.security import authorize_scope, filter_secrets, security_projection

ROOT = Path(__file__).resolve().parents[3]


def test_repository_and_package_structure() -> None:
    assert (ROOT / ".git").is_dir()
    assert (ROOT / "src" / "tkai" / "v11").is_dir()
    required = {
        "autonomous_core",
        "intelligence",
        "knowledge",
        "reasoning",
        "decision",
        "planning",
        "operations",
        "recovery",
        "governance",
        "trust",
        "integrity",
        "compatibility",
        "contexts",
        "registries",
        "relationships",
        "contracts",
        "interfaces",
        "validation",
        "diagnostics",
        "health",
        "metrics",
        "audit",
        "security",
        "events",
        "dashboard",
        "api",
    }
    assert required <= {path.name for path in (ROOT / "src/tkai/v11").iterdir()}


def test_core_model_is_complete_immutable_and_advisory() -> None:
    model = AutonomousCoreModel()
    assert model.core_id == "tkai-v11-autonomous-intelligence-core"
    assert model.version == "11.0.0"
    assert model.advisory and model.deterministic and model.read_only
    assert not model.executable
    with pytest.raises(FrozenInstanceError):
        model.health = "changed"  # type: ignore[misc]


def test_intelligence_profile_contract_and_confidence_validation() -> None:
    profile = IntelligenceProfile(
        objectives=("assess",),
        evidence_references=("evidence:1",),
        confidence=0.75,
    )
    core = AutonomousIntelligenceCore(AutonomousCoreModel(intelligence_profile=profile))
    result = core.profile()
    assert result["confidence"] == 0.75
    assert result["hidden_reasoning"] is False
    assert result["execution"] == "disabled"
    with pytest.raises(ValueError, match="confidence"):
        AutonomousIntelligenceCore(
            AutonomousCoreModel(
                intelligence_profile=IntelligenceProfile(confidence=1.1)
            )
        )


def test_cross_version_references_are_complete_and_read_only() -> None:
    assert SUPPORTED_GENERATIONS == ("v6", "v7", "v8", "v9", "v10", "v11")
    assert len(V10_REFERENCES) == 11
    projection = AutonomousIntelligenceCore().compatibility()
    assert projection["backward_compatible"] is True
    assert projection["mutation"] is False


def test_security_redaction_isolation_and_forbidden_capabilities() -> None:
    assert filter_secrets({"token": "value", "safe": {"password": "value"}}) == {
        "token": "[REDACTED]",
        "safe": {"password": "[REDACTED]"},
    }
    with pytest.raises(PermissionError, match="tenant"):
        authorize_scope(Scope(tenant="one"), Scope(tenant="two"))
    projection = security_projection()
    assert projection["tenant_isolation"] and projection["workspace_isolation"]
    assert not projection["hidden_reasoning_exposed"]
    assert not projection["runtime_mutation"]
    assert not projection["tiktok_action"]


def test_dashboard_is_a_read_only_projection() -> None:
    snapshot = dashboard_snapshot(AutonomousIntelligenceCore())
    assert len(DASHBOARD_SECTIONS) == 18
    assert snapshot["read_only"] is True
    assert snapshot["actions"] == ()


def test_api_has_exactly_nineteen_get_only_routes() -> None:
    core = AutonomousIntelligenceCore()
    assert len(GET_ROUTES) == 19
    assert set(route_handlers(core)) == set(GET_ROUTES)
    paths = openapi_contract()["paths"]
    assert isinstance(paths, dict)
    assert all(set(operations) == {"get"} for operations in paths.values())
    assert all(
        method not in operations
        for operations in paths.values()
        for method in FORBIDDEN_METHODS
    )


def test_api_contains_no_forbidden_endpoint() -> None:
    forbidden = (
        "execute",
        "action",
        "login",
        "browser",
        "deploy",
        "schedule",
        "allocate",
        "mutate",
        "control",
        "tiktok",
    )
    assert not any(term in path for path in GET_ROUTES for term in forbidden)


def test_validation_diagnostics_health_metrics_and_audit() -> None:
    core = AutonomousIntelligenceCore()
    assert core.validation()["valid"] is True
    assert core.diagnostics()["status"] == "clear"
    assert core.health()["status"] == "healthy"
    assert core.metrics()["v11_intelligence_reference_domains_total"] == 9
    assert core.audit() == {"items": [], "append_enabled": False}


def test_aggregate_openapi_registers_v11_without_mutating_legacy_routes() -> None:
    schema = create_app().openapi()
    assert set(GET_ROUTES) <= set(schema["paths"])
    for path in GET_ROUTES:
        assert set(schema["paths"][path]) == {"get"}
    assert "/v10/core" in schema["paths"]
    assert any(path.startswith("/v9/") for path in schema["paths"])
    assert any(path.startswith("/v8/") for path in schema["paths"])
    assert any(path.startswith("/v7/") for path in schema["paths"])
    assert "v6" in SUPPORTED_GENERATIONS
