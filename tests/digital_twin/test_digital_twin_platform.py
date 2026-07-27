import pytest

from digital_twin import (
    DigitalTwin,
    DigitalTwinPlatform,
    EntityType,
    Optimization,
    OptimizationType,
    Prediction,
    PredictionType,
    RelationshipType,
    SynchronizationMode,
    SyncPolicy,
    TelemetryRecord,
    TwinEntity,
    TwinRelationship,
    TwinScope,
    TwinStatus,
)
from digital_twin.dashboard import SECTIONS


@pytest.fixture
def system() -> tuple[DigitalTwinPlatform, TwinScope]:
    platform = DigitalTwinPlatform()
    scope = TwinScope(
        "tenant-a", "workspace-a", "owner", frozenset({"digital_twin:admin"})
    )
    platform.create_twin(
        DigitalTwin(
            "twin-1",
            "Factory",
            "Factory twin",
            scope.tenant,
            scope.workspace,
            scope.actor,
            "system",
        ),
        scope,
    )
    return platform, scope


def test_twin_lifecycle_and_isolation(
    system: tuple[DigitalTwinPlatform, TwinScope],
) -> None:
    platform, scope = system
    for status in (
        TwinStatus.PROVISIONED,
        TwinStatus.SYNCHRONIZED,
        TwinStatus.RUNNING,
        TwinStatus.PAUSED,
        TwinStatus.ARCHIVED,
        TwinStatus.DELETED,
    ):
        assert platform.set_status("twin-1", status, scope).status is status
    other = TwinScope(
        "tenant-b", "workspace-a", "attacker", frozenset({"digital_twin:admin"})
    )
    with pytest.raises(PermissionError):
        platform.set_status("twin-1", TwinStatus.RUNNING, other)
    assert platform.audit


def test_entities_relationships_and_topology(
    system: tuple[DigitalTwinPlatform, TwinScope],
) -> None:
    platform, scope = system
    platform.add_entity(
        TwinEntity(
            "machine", "twin-1", scope.tenant, scope.workspace, "M1",
            EntityType.MACHINE,
        ),
        scope,
    )
    platform.add_entity(
        TwinEntity(
            "model", "twin-1", scope.tenant, scope.workspace, "Predictor",
            EntityType.MODEL,
        ),
        scope,
    )
    platform.add_relationship(
        TwinRelationship(
            "rel-1",
            "twin-1",
            scope.tenant,
            scope.workspace,
            "model",
            "machine",
            RelationshipType.ASSOCIATION,
        ),
        scope,
    )
    graph = platform.topology("twin-1", scope)
    assert len(graph["entities"]) == 2
    assert graph["relationships"][0]["type"] == "association"


def test_state_synchronization_diff_and_failure_metric(
    system: tuple[DigitalTwinPlatform, TwinScope],
) -> None:
    platform, scope = system
    platform.set_state("twin-1", {"load": 10}, {"load": 8}, scope)
    policy = SyncPolicy(
        "sync-1",
        "twin-1",
        scope.tenant,
        scope.workspace,
        SynchronizationMode.EVENT_DRIVEN,
    )
    platform.configure_sync(policy, scope)
    snapshot = platform.synchronize(
        "twin-1", {"load": 9}, scope, expected_version=1
    )
    assert snapshot.version == 2
    assert platform.state_diff("twin-1", 1, 2, scope)["load"]["after"] == 9
    with pytest.raises(ValueError, match="conflict"):
        platform.synchronize("twin-1", {"load": 7}, scope, expected_version=1)
    metrics = platform.metrics.snapshot()
    assert metrics["twin_sync_total"] == 1
    assert metrics["twin_sync_failures_total"] == 1


def test_simulation_prediction_optimization_dashboard_and_metrics(
    system: tuple[DigitalTwinPlatform, TwinScope],
) -> None:
    platform, scope = system
    platform.set_state("twin-1", {"capacity": 50}, {"capacity": 80}, scope)
    run = platform.run_simulation(
        "twin-1", {"capacity": 90}, scope, rollback_plan={"capacity": 50}
    )
    assert run.impact["capacity"]["after"] == 90
    platform.add_prediction(
        Prediction(
            "p-1", "twin-1", scope.tenant, scope.workspace,
            PredictionType.CAPACITY, 90, 0.9, "P7D",
        ),
        scope,
    )
    platform.add_optimization(
        Optimization(
            "o-1", "twin-1", scope.tenant, scope.workspace,
            OptimizationType.ENERGY_INTERFACE, {"reduce_watts": 20}, 0.2,
        ),
        scope,
    )
    dashboard = platform.dashboard(scope)
    assert set(SECTIONS) <= dashboard.keys()
    assert dashboard["predictions"][0]["type"] == "capacity"
    rendered = platform.metrics.render_prometheus()
    for metric in (
        "digital_twins_total",
        "simulation_runs_total",
        "prediction_total",
        "optimization_total",
    ):
        assert metric in rendered


def test_telemetry_rejects_secrets(
    system: tuple[DigitalTwinPlatform, TwinScope],
) -> None:
    platform, scope = system
    with pytest.raises(ValueError, match="Secrets"):
        platform.record_telemetry(
            TelemetryRecord(
                "telemetry-1",
                "twin-1",
                scope.tenant,
                scope.workspace,
                events=("healthy",),
                capacity={"api_token": 1},
            ),
            scope,
        )
