"""Offline V12 platform, safety, compatibility, and API tests."""

from __future__ import annotations

import pytest

from tkai.v12 import (
    AgentProfile,
    AgentType,
    BoundedRegistry,
    DependencyAnalyzer,
    DiscoveryPolicy,
    LocalDiscovery,
    MemoryProfile,
    MemoryType,
    V12Platform,
    validate_platform,
)
from tkai.v12.api import FORBIDDEN_METHODS, GET_ROUTES, openapi_contract, route_handlers
from tkai.v12.compatibility import compatibility_matrix
from tkai.v12.dashboard import dashboard_manifest


def test_complete_component_inventory_is_deterministic_and_non_executable() -> None:
    platform = V12Platform()
    assert platform.overview()["component_count"] == 28
    assert platform.overview() == platform.overview()
    for component in platform.overview()["components"]:
        assert component["architecture"]["read_only"]
        assert not any(component["execution"].values())


def test_complete_api_inventory_is_get_only() -> None:
    schema = openapi_contract()
    assert len(GET_ROUTES) == len(set(GET_ROUTES))
    assert tuple(schema["paths"]) == GET_ROUTES
    assert all(set(operations) == {"get"} for operations in schema["paths"].values())
    assert FORBIDDEN_METHODS == ("POST", "PUT", "PATCH", "DELETE")
    assert tuple(route_handlers(V12Platform())) == GET_ROUTES


def test_registry_enforces_tenant_workspace_and_namespace_isolation() -> None:
    registry: BoundedRegistry[AgentProfile] = BoundedRegistry(maximum_items=2)
    agent = registry.register(AgentProfile(id="a", name="A", agent_type=AgentType.MOCK))
    assert registry.get("a") == agent
    with pytest.raises(KeyError):
        registry.get("a", tenant="other")


def test_discovery_is_allowlisted_and_bounded() -> None:
    agent = AgentProfile(id="a", name="A")
    discovery = LocalDiscovery(
        DiscoveryPolicy(frozenset({"fixture"}), maximum_results=1)
    )
    assert discovery.discover({"fixture": [agent]}) == (agent,)
    with pytest.raises(ValueError):
        discovery.discover({"remote": [agent]})


def test_secret_and_hidden_reasoning_metadata_are_rejected() -> None:
    for field in (
        "api_key",
        "password",
        "cookie",
        "session",
        "chain_of_thought",
        "private_scratchpad",
        "hidden_prompt",
        "system_message",
    ):
        with pytest.raises(ValueError):
            AgentProfile(id="a", name="A", safe_metadata={field: "unsafe"})


def test_memory_is_metadata_only_and_secret_safe() -> None:
    memory = MemoryProfile(
        id="m",
        name="Memory",
        memory_type=MemoryType.WORKING,
        subject_reference="agent:a",
    )
    assert memory.projection()["execution_enabled"] is False
    assert memory.retention_metadata == "bounded"


def test_dependency_analysis_detects_missing_and_circular_dependencies() -> None:
    findings = DependencyAnalyzer().analyze({"a": ("b",), "b": ("a", "missing")})
    assert {"missing-dependency", "circular-dependency"} <= {
        item.kind for item in findings
    }


def test_historical_compatibility_adapters_are_read_only() -> None:
    matrix = compatibility_matrix()
    assert tuple(item["version"] for item in matrix) == (6, 7, 8, 9, 10, 11)
    assert all(item["read_only"] and not item["mutation_enabled"] for item in matrix)


def test_validation_health_metrics_dashboard_and_observability() -> None:
    assert validate_platform().valid
    assert V12Platform().health()["status"] == "Healthy"
    assert V12Platform().readiness()["execution_ready"] is False
    assert V12Platform().liveness()["external_dependencies"] == ()
    assert V12Platform().metrics()["v12_platform_components_total"] == 28
    assert dashboard_manifest()["read_only"]
