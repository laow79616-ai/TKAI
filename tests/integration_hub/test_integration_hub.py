import pytest

from integration_hub import (
    METRICS,
    Connector,
    ConnectorCategory,
    ConnectorInstance,
    ConnectorStatus,
    CredentialReference,
    HealthRecord,
    HubScope,
    IntegrationFlow,
    IntegrationHub,
    IntegrationPolicy,
    IntegrationTemplate,
    Mapping,
    Schedule,
    ScheduleType,
)
from integration_hub.dashboard import SECTIONS


@pytest.fixture
def system() -> tuple[IntegrationHub, HubScope]:
    hub = IntegrationHub()
    scope = HubScope(
        "tenant-a",
        "workspace-a",
        "alice",
        frozenset({"integration_hub:admin"}),
    )
    for connector_id in ("source", "target"):
        hub.create_connector(
            Connector(
                connector_id,
                connector_id.title(),
                "reference",
                ConnectorCategory.CRM,
                "1.0",
                ("read", "write"),
                scope.tenant,
                scope.workspace,
            ),
            scope,
        )
        hub.set_connector_status(
            connector_id, ConnectorStatus.CONFIGURED, scope
        )
        hub.set_connector_status(
            connector_id, ConnectorStatus.VALIDATED, scope
        )
        hub.set_connector_status(connector_id, ConnectorStatus.ENABLED, scope)
        credential_id = f"credential-{connector_id}"
        hub.add_credential(
            CredentialReference(
                credential_id,
                scope.tenant,
                scope.workspace,
                oauth2_reference=f"vault://hub/{connector_id}",
                rotation_interface="vault",
            ),
            scope,
        )
        hub.create_instance(
            ConnectorInstance(
                connector_id,
                scope.tenant,
                scope.workspace,
                scope.actor,
                connector_id,
                credential_id,
            ),
            scope,
        )
    hub.create_mapping(
        Mapping(
            "mapping",
            scope.tenant,
            scope.workspace,
            {"name": "string"},
            {"display_name": "string"},
            {"name": "display_name"},
            required_fields=("name",),
            transformations={"name": "upper"},
        ),
        scope,
    )
    hub.create_policy(
        IntegrationPolicy(
            "policy", scope.tenant, scope.workspace, retry_limit=2
        ),
        scope,
    )
    hub.create_schedule(
        Schedule(
            "schedule",
            scope.tenant,
            scope.workspace,
            ScheduleType.CRON,
            "0 * * * *",
            "run_once",
            "UTC",
        ),
        scope,
    )
    hub.create_flow(
        IntegrationFlow(
            "flow",
            scope.tenant,
            scope.workspace,
            "source",
            "target",
            "schedule",
            "mapping",
            "policy",
            schedule_id="schedule",
            status=ConnectorStatus.ENABLED,
        ),
        scope,
    )
    return hub, scope


def test_catalog_lifecycle_instances_scheduling_and_isolation(system) -> None:
    hub, scope = system
    assert len(hub.dashboard(scope)["catalog"]) == 2
    assert hub.instances["source"].owner == "alice"
    assert hub.schedules["schedule"].timezone == "UTC"
    with pytest.raises(ValueError, match="lifecycle"):
        hub.set_connector_status("source", ConnectorStatus.DRAFT, scope)
    foreign = HubScope(
        "tenant-b",
        "workspace-a",
        "mallory",
        frozenset({"integration_hub:admin"}),
    )
    assert hub.dashboard(foreign)["connectors"] == []
    with pytest.raises(PermissionError):
        hub.set_connector_status("source", ConnectorStatus.DISABLED, foreign)


def test_mapping_flow_idempotency_analytics_and_metrics(system) -> None:
    hub, scope = system
    calls = 0

    def adapter(payload: dict[str, object]) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return payload

    hub.register_handler("target", adapter, scope)
    first = hub.execute("flow", {"name": "Ada"}, scope, idempotency_key="run-1")
    second = hub.execute("flow", {"name": "Ada"}, scope, idempotency_key="run-1")
    assert first == second == {"display_name": "ADA"}
    assert calls == 1
    assert hub.dashboard(scope)["analytics"]["successes"] == 1
    assert set(hub.metrics.snapshot()) == set(METRICS)
    assert "integration_hub_runs_total" in hub.metrics.render_prometheus()


def test_retries_dead_letter_health_and_dashboard(system) -> None:
    hub, scope = system
    hub.register_handler(
        "target",
        lambda payload: (_ for _ in ()).throw(RuntimeError("down")),
        scope,
    )
    with pytest.raises(RuntimeError, match="run_id"):
        hub.execute("flow", {"name": "Ada"}, scope)
    assert len(hub.dead_letters) == 1
    assert hub.metrics.snapshot()["integration_hub_retries_total"] == 2
    hub.record_health(
        HealthRecord(
            "target", scope.tenant, scope.workspace, True, True, 0.01, 0
        ),
        scope,
    )
    dashboard = hub.dashboard(scope)
    assert set(dashboard) == set(SECTIONS)
    assert dashboard["health"][0]["status"] == "healthy"


def test_credentials_mapping_payload_and_log_security(system) -> None:
    hub, scope = system
    with pytest.raises(ValueError, match="opaque"):
        CredentialReference(
            "bad", scope.tenant, scope.workspace, api_key_reference="plaintext"
        )
    with pytest.raises(ValueError, match="declarative"):
        Mapping(
            "unsafe",
            scope.tenant,
            scope.workspace,
            {},
            {},
            {},
            transformations={"x": "eval"},
        )
    with pytest.raises(ValueError, match="Secrets"):
        hub.execute("flow", {"name": "Ada", "api_key": "bad"}, scope)
    assert "plaintext" not in repr(hub.audit)


def test_template_import_export_clone_and_version(system) -> None:
    hub, scope = system
    imported = hub.import_template(
        IntegrationTemplate(
            "crm-template",
            scope.tenant,
            scope.workspace,
            "connector",
            "1",
            {"provider": "reference", "category": "crm"},
        ),
        scope,
    )
    assert hub.export_template(imported.id, scope)["version"] == "1"
    clone = hub.clone_template(imported.id, "crm-template-v2", "2", scope)
    assert clone.version == "2"
    assert clone.metadata["cloned_from"] == imported.id
