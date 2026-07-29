from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tkai.v7.data_framework import (
    ArchivePlan,
    DataModel,
    DataQuery,
    DataRecord,
    DataSchema,
    Filter,
    FilterOperator,
    IndexDefinition,
    Lifecycle,
    MigrationAssessment,
    Pagination,
    RepositoryDefinition,
    RetentionPolicy,
    SchemaField,
    Scope,
    SortDirection,
    SortField,
    StorageAdapter,
    StorageKind,
    TransactionMetadata,
    UnifiedDataFramework,
    ValidationError,
    ValidationStatus,
    payload_digest,
    serialize,
)
from tkai.v7.data_framework.api import DATA_ENDPOINTS, register_data_framework_routes
from tkai.v7.data_framework.dashboard import DASHBOARD_SECTIONS, DataDashboard


def populated() -> tuple[UnifiedDataFramework, Scope]:
    framework = UnifiedDataFramework()
    scope = Scope("tenant-a", "workspace-a", "catalog")
    framework.register_schema(
        DataSchema(
            "profile",
            scope,
            "1.0.0",
            (
                SchemaField("name", "string", required=True, indexed=True),
                SchemaField("age", "integer", minimum=0, maximum=150),
                SchemaField("credential", "reference", secret=True),
            ),
        )
    )
    framework.register_repository(RepositoryDefinition("profiles", scope, "1.0.0"))
    framework.register_adapter(
        StorageAdapter("memory", scope, StorageKind.MEMORY, "1.0.0")
    )
    framework.register_model(
        DataModel(
            "profile",
            "Profile",
            "Local profile metadata",
            scope,
            "tkai",
            "1.0.0",
            "profile:1.0.0",
            "profiles:1.0.0",
            "memory:1.0.0",
            lifecycle=Lifecycle.AVAILABLE,
        )
    )
    return framework, scope


def test_models_records_are_immutable_reference_only_and_redacted() -> None:
    framework, scope = populated()
    payload = b"bounded fixture"
    record = DataRecord(
        "record-a",
        "profile",
        scope,
        "1.0.0",
        "1.0.0",
        "payload://fixture/a",
        payload_digest(payload),
    )
    framework.validate_record(record, payload)
    with pytest.raises((AttributeError, TypeError)):
        record.record_id = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError):
        DataRecord(
            "unsafe",
            "profile",
            scope,
            "1.0.0",
            "1.0.0",
            "plaintext-secret",
            payload_digest(payload),
        )
    assert serialize({"password": "nope"})["password"] == "[REDACTED]"


def test_schema_aware_bounded_queries_filters_sorting_and_pagination() -> None:
    framework, scope = populated()
    query = DataQuery(
        "query-a",
        "profile",
        scope,
        filters=(Filter("name", FilterOperator.PREFIX, "A"),),
        sort_order=(SortField("name", SortDirection.ASCENDING),),
        pagination=Pagination(page_size=25),
        projection_fields=("name",),
        maximum_results=50,
    )
    framework.register_query(query)
    with pytest.raises(ValidationError):
        framework.register_query(
            DataQuery("bad", "profile", scope, projection_fields=("password",))
        )
    with pytest.raises(ValueError):
        Pagination(page_size=101)
    with pytest.raises(ValueError):
        DataQuery("huge", "profile", scope, maximum_results=1001)
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError):
        DataQuery("long", "profile", scope, time_range=(now, now + timedelta(days=367)))


def test_storage_is_local_and_index_transaction_operations_are_advisory() -> None:
    framework, scope = populated()
    assert {kind.value for kind in StorageKind} == {
        "memory",
        "local-file",
        "sqlite-metadata",
        "repository",
        "v6-database",
        "snapshot",
        "test",
        "mock",
    }
    with pytest.raises(ValueError):
        StorageAdapter("cloud", scope, StorageKind.MOCK, "1.0.0", "https://cloud")
    with pytest.raises(ValidationError):
        framework.register_index(
            IndexDefinition(
                "idx", scope, "1.0.0", "primary", ("name",), planning_only=False
            )
        )
    with pytest.raises(ValidationError):
        framework.register_transaction(
            TransactionMetadata(
                "tx", scope, ("profiles",), "serializable", "draft", distributed=True
            )
        )


def test_retention_archival_and_migration_never_execute() -> None:
    framework, scope = populated()
    with pytest.raises(ValidationError):
        framework.register_retention_policy(
            RetentionPolicy("bad", scope, "1.0.0", "active", 30, destructive_purge=True)
        )
    with pytest.raises(ValidationError):
        framework.plan_archive(
            ArchivePlan(
                "archive",
                scope,
                "profiles",
                "all",
                None,
                "retain",
                "integrity",
                ValidationStatus.VALID,
                "approval://a",
                "planned",
                executable=True,
            )
        )
    with pytest.raises(ValidationError):
        framework.assess_migration(
            MigrationAssessment(
                "migration",
                scope,
                "1",
                "2",
                {},
                True,
                True,
                ("map",),
                ("restore",),
                "low",
                "approval://a",
                "ready",
                executable=True,
            )
        )


def test_isolation_events_metrics_health_dashboard_and_compatibility() -> None:
    framework, scope = populated()
    other = Scope("tenant-b", "workspace-a", "catalog")
    assert framework.projection("models", other) == []
    assert framework.health(scope)["external_connections_enabled"] is False
    assert framework.events[0]["fabric"] == "v7.event_fabric"
    assert framework.compatibility()["v6"] is True
    snapshot = DataDashboard(framework).snapshot(scope)
    assert set(snapshot) == set(DASHBOARD_SECTIONS)
    for forbidden in (
        "delete",
        "purge",
        "migrate",
        "execute_sql",
        "create_index",
        "connect_remote",
    ):
        assert not hasattr(framework, forbidden)


def test_get_only_api_and_openapi() -> None:
    framework, _ = populated()
    app = FastAPI()
    register_data_framework_routes(app, framework)
    client = TestClient(app)
    params = {"tenant": "tenant-a", "workspace": "workspace-a", "namespace": "catalog"}
    paths = app.openapi()["paths"]
    for endpoint in DATA_ENDPOINTS:
        path = f"/v7/data/{endpoint}"
        assert client.get(path, params=params).status_code == 200
        assert client.post(path, params=params).status_code == 405
        assert set(paths[path]) == {"get"}
    forbidden = (
        "sql",
        "write",
        "delete",
        "migrate/execute",
        "schemas/update",
        "secrets",
    )
    assert not any(any(item in path for item in forbidden) for path in paths)


def test_v6_and_v7_framework_imports_remain_available() -> None:
    import tkai
    import tkai.v7.ai_framework
    import tkai.v7.configuration_framework
    import tkai.v7.event_fabric
    import tkai.v7.extension_framework
    import tkai.v7.observability_framework
    import tkai.v7.resource_framework
    import tkai.v7.security_framework
    import tkai.v7.state_framework
    import tkai.v7.workflow_framework

    assert tkai
