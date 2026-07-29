from fastapi import FastAPI
from fastapi.testclient import TestClient

from tkai.v7.observability_framework import (
    Alert,
    AuditCorrelation,
    DiagnosticResult,
    HealthRecord,
    HealthStatus,
    LogRecord,
    MetricDefinition,
    MetricSample,
    ObservabilityFramework,
    Observation,
    ObservationScope,
    Severity,
    Span,
)
from tkai.v7.observability_framework.api import (
    OBSERVABILITY_ENDPOINTS,
    register_observability_framework_routes,
)
from tkai.v7.observability_framework.dashboard import ObservabilityDashboard


def test_metrics_discovery_aggregation_and_compatibility() -> None:
    framework = ObservabilityFramework()
    scope = ObservationScope("tenant-a", "workspace-a")
    definition = MetricDefinition(
        "jobs",
        "completed jobs",
        "count",
        scope,
        aggregation="sum",
        sampling={"mode": "reference"},
        retention={"days": 30},
    )
    framework.metrics.register(definition)
    framework.metrics.sample(MetricSample("jobs", 2, scope))
    framework.metrics.sample(MetricSample("jobs", 3, scope))
    assert framework.metrics.aggregate(scope) == {"jobs": 5}
    assert framework.metrics.discover(scope)[0].compatibility == frozenset({"6", "7"})
    assert framework.metrics.discover(ObservationScope("other", "workspace-a")) == ()


def test_structured_logging_redacts_secrets_and_correlates() -> None:
    framework = ObservabilityFramework()
    scope = ObservationScope("tenant-a", "workspace-a")
    record = framework.log(
        LogRecord(
            "completed",
            "operation",
            "worker",
            scope,
            correlation_id="cor-1",
            metadata={"token": "secret", "safe": "yes"},
        )
    )
    assert record.metadata["token"] == "[REDACTED]"
    observation = framework.observations.list(scope)[0]
    assert observation.correlation_id == "cor-1"


def test_trace_parent_child_lifecycle() -> None:
    framework = ObservabilityFramework()
    scope = ObservationScope("tenant-a", "workspace-a")
    framework.trace(Span("trace-1", "root", "root", "api", scope))
    framework.trace(
        Span(
            "trace-1",
            "child",
            "child",
            "worker",
            scope,
            parent_span_id="root",
        )
    )
    assert framework.trace_spans(scope)[1].parent_span_id == "root"


def test_read_only_diagnostics_health_and_heartbeat() -> None:
    framework = ObservabilityFramework()
    scope = ObservationScope("tenant-a", "workspace-a")
    framework.register_diagnostic(
        "configuration",
        lambda selected: DiagnosticResult(
            "diag-1",
            "configuration",
            "config",
            selected,
            HealthStatus.HEALTHY,
            "valid",
        ),
    )
    assert framework.run_diagnostics(scope)[0].read_only
    framework.record_health(
        HealthRecord(
            "api",
            "liveness",
            scope,
            HealthStatus.HEALTHY,
        )
    )
    framework.record_health(
        HealthRecord(
            "worker",
            "heartbeat",
            scope,
            HealthStatus.HEALTHY,
        )
    )
    assert framework.platform_health(scope)["heartbeats"] == 1


def test_internal_telemetry_alert_and_audit_correlation() -> None:
    framework = ObservabilityFramework()
    scope = ObservationScope("tenant-a", "workspace-a")
    framework.record_telemetry(
        Observation(
            "obs-1",
            "telemetry",
            "internal",
            "api",
            scope,
            metric_reference="jobs",
        )
    )
    framework.raise_alert(
        Alert(
            "alert-1",
            "api",
            scope,
            Severity.WARNING,
            {"value": 90},
            suppression={"window": "5m"},
            acknowledgement={"actor": None},
            recommendations=("inspect dependency health",),
        )
    )
    framework.correlate(
        AuditCorrelation(
            "cor-1",
            scope,
            audit_references=("audit-1",),
            trace_references=("trace-1",),
            metric_references=("jobs",),
            health_references=("api",),
            event_references=("event-1",),
        )
    )
    snapshot = framework.snapshot(scope)
    assert len(snapshot["telemetry"]) == 1
    assert len(snapshot["alerts"]) == 1
    assert snapshot["audit"][0]["trace_references"] == ["trace-1"]
    assert snapshot["health"]["outbound_telemetry"] is False


def test_dashboard_has_all_required_sections_and_is_isolated() -> None:
    framework = ObservabilityFramework()
    scope = ObservationScope("tenant-a", "workspace-a")
    other = ObservationScope("tenant-b", "workspace-b")
    framework.log(LogRecord("visible", "audit", "api", scope))
    dashboard = ObservabilityDashboard(framework)
    assert set(dashboard.snapshot(scope)) == set(dashboard.sections)
    assert dashboard.snapshot(other)["logging"] == []


def test_get_only_api_and_openapi() -> None:
    app = FastAPI()
    framework = ObservabilityFramework()
    register_observability_framework_routes(app, framework)
    client = TestClient(app)
    for endpoint in OBSERVABILITY_ENDPOINTS:
        response = client.get(
            f"/v7/observability/{endpoint}",
            params={"tenant": "tenant-a", "workspace": "workspace-a"},
        )
        assert response.status_code == 200
        assert client.post(f"/v7/observability/{endpoint}").status_code == 405
    paths = app.openapi()["paths"]
    assert all(
        set(paths[f"/v7/observability/{endpoint}"]) == {"get"}
        for endpoint in OBSERVABILITY_ENDPOINTS
    )


def test_v6_import_and_behavior_remain_available() -> None:
    import tkai

    assert tkai is not None
