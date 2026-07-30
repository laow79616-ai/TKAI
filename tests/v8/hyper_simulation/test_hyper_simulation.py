"""Offline mock-only tests for V8 Hyper Simulation & Forecasting."""

from dataclasses import FrozenInstanceError

import pytest

from tkai.v8.hyper_simulation.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v8.hyper_simulation.contracts import (
    AssumptionMetadata,
    DependencyKind,
    DependencyMetadata,
    ForecastMetadata,
    InputMetadata,
    ModelKind,
    ModelMetadata,
    ScenarioKind,
    ScenarioMetadata,
    SimulationLifecycle,
    SimulationMetadata,
    SimulationProfile,
    SimulationReference,
    SimulationScope,
    TrendKind,
    TrendMetadata,
    UncertaintyMetadata,
)
from tkai.v8.hyper_simulation.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v8.hyper_simulation.fabric import HyperSimulationFabric
from tkai.v8.hyper_simulation.security import (
    SimulationAccessController,
    SimulationPrincipal,
)


def ref(identifier: str, generation: str = "v8") -> SimulationReference:
    return SimulationReference(identifier, "1.0.0", generation)


def test_profile_lifecycle_immutable_and_non_executable() -> None:
    profile = SimulationProfile(
        "profile-1",
        "Mock profile",
        owner="team",
        lifecycle=SimulationLifecycle.APPROVED_REFERENCE,
        time_horizon=30,
    )
    fabric = HyperSimulationFabric()
    fabric.register_profile(profile)
    assert fabric.snapshot()["profiles"][0]["execution_authorized"] is False
    assert len(SimulationLifecycle) == 13
    with pytest.raises(FrozenInstanceError):
        profile.owner = "other"  # type: ignore[misc]


def test_reference_only_inputs_models_forecasts_and_assumptions() -> None:
    fabric = HyperSimulationFabric()
    with pytest.raises(ValueError, match="reference-only"):
        InputMetadata("bad", ref("source"), "metric", ref("subject"))
    item = InputMetadata(
        "input-1",
        ref("source"),
        "metric",
        ref("subject"),
        value_reference=ref("value"),
        freshness=1,
        reliability=1,
        confidence=0.8,
    )
    fabric.register_input(item)
    with pytest.raises(ValueError, match="arbitrary"):
        ModelMetadata("bad", ModelKind.DETERMINISTIC, algorithm="python:eval")
    fabric.register_model(ModelMetadata("model-1", ModelKind.DETERMINISTIC))
    fabric.register_scenario(
        ScenarioMetadata("scenario-1", ScenarioKind.EXPECTED, "Expected")
    )
    fabric.register_uncertainty(
        UncertaintyMetadata("uncertainty-1", "input", 0.2, "Mock uncertainty")
    )
    forecast = ForecastMetadata(
        "forecast-1",
        ref("profile-1"),
        ref("subject"),
        "trend",
        2,
        ref("baseline"),
        ref("scenario-1"),
        ref("model-1"),
        ref("estimate"),
        uncertainty_references=(ref("uncertainty-1"),),
        limitations=("Mock-only evidence",),
    )
    fabric.register_forecast(forecast)
    assumption = AssumptionMetadata("a-1", "Mock assumption", ref("source"))
    fabric.register_assumption(assumption)
    assert forecast.advisory is True
    assert assumption.is_fact is False


def test_bounded_deterministic_offline_simulation() -> None:
    fabric = HyperSimulationFabric()
    assert fabric.deterministic_forecast((1.0, 2.0, 3.0), 2) == (4.0, 5.0)
    with pytest.raises(ValueError, match="horizon"):
        fabric.deterministic_forecast((1.0,), fabric.MAX_TIME_HORIZON + 1)
    simulation = SimulationMetadata(
        "run-1", ref("profile"), ref("scenario"), ref("model"), ("timeline",)
    )
    fabric.register_simulation(simulation)
    assert fabric.snapshot()["simulations"][0]["offline_only"] is True
    assert fabric.executes_tiktok_actions() is False
    assert fabric.mutates_runtime_state() is False
    assert fabric.schedules_runtime_work() is False
    assert fabric.allocates_resources() is False
    assert fabric.authorizes_execution() is False
    assert fabric.uses_external_models() is False


def test_dependencies_trends_and_no_causal_claims() -> None:
    fabric = HyperSimulationFabric()
    fabric.register_dependency(
        DependencyMetadata("d1", DependencyKind.SEQUENTIAL, ref("a"), ref("b"))
    )
    fabric.register_dependency(
        DependencyMetadata("d2", DependencyKind.SEQUENTIAL, ref("b"), ref("a"))
    )
    assert any(item["code"] == "circular-dependency" for item in fabric.diagnostics())
    with pytest.raises(ValueError, match="causal"):
        TrendMetadata(
            "trend-1", TrendKind.INCREASING, ref("subject"), causal_claim=True
        )


def test_sources_security_isolation_and_secret_filtering() -> None:
    fabric = HyperSimulationFabric(metadata={"api_key": "hidden", "safe": "visible"})
    values = fabric.aggregate_metadata(
        "v8-hyper-kernel", ({"token": "x", "id": "one"},)
    )
    assert values[0]["token"] == "[REDACTED]"
    assert fabric.source_adapter("v8-hyper-kernel").read_only is True
    with pytest.raises(PermissionError):
        fabric.source_adapter("internet")
    scope = SimulationScope("tenant-a", "workspace-a", "namespace-a", "profile-a")
    principal = SimulationPrincipal(
        "reader",
        tenant="tenant-a",
        workspace="workspace-a",
        namespaces=frozenset({"namespace-a"}),
        profiles=frozenset({"profile-a"}),
    )
    SimulationAccessController().authorize(principal, "simulation:read", scope)
    with pytest.raises(PermissionError):
        SimulationAccessController().authorize(
            principal, "simulation:read", SimulationScope("tenant-b")
        )


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, str] = {}

    def add_api_route(
        self, path: str, _handler: object, *, methods: list[str], tags: list[str]
    ) -> None:
        assert tags == ["V8 Hyper Simulation"]
        self.routes[path] = methods[0]


def test_get_only_api_dashboard_health_metrics_and_openapi() -> None:
    fabric = HyperSimulationFabric()
    app = FakeApp()
    register_routes(app, fabric)
    assert set(app.routes) == set(GET_ROUTES)
    assert set(app.routes.values()) == {"GET"}
    assert len(GET_ROUTES) == 31
    assert all(set(value) == {"get"} for value in openapi_contract()["paths"].values())
    assert dashboard_snapshot(fabric)["read_only"] is True
    assert len(DASHBOARD_SECTIONS) == 32
    assert fabric.health()["network_access"] == "disabled"
    assert set(fabric.metrics()) >= {
        "v8_simulation_profiles_total",
        "v8_simulation_forecasts_total",
        "v8_simulation_health_status",
    }
