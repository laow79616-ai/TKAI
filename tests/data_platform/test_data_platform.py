from __future__ import annotations

import pytest

from data_platform import (
    SECTIONS,
    Classification,
    ConnectorRequest,
    DataPlatform,
    DataScope,
    LineageEdge,
    MemoryConnector,
    ObjectStorage,
    QualityRule,
    compatible,
    migrate,
    validate_schema,
)
from data_platform.api import register_data_routes


def payload(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "id": "data-1",
        "name": "Customers",
        "description": "Customer records",
        "owner": "alice",
        "tenant": "tenant-a",
        "workspace": "workspace-a",
        "classification": "confidential",
        "version": "1.0.0",
        "schema": {
            "fields": {"id": "string", "email": "string"},
            "required": ["id", "email"],
        },
        "metadata": {"source": "crm"},
        "tags": ["customer"],
        "domain": "sales",
    }
    value.update(changes)
    return value


def test_dataset_lifecycle_catalog_and_isolation() -> None:
    platform = DataPlatform()
    scope = DataScope("tenant-a", "workspace-a")
    item = platform.create_dataset(payload())
    assert item.classification is Classification.CONFIDENTIAL
    assert platform.list_datasets(
        scope,
        "customer",
        tags=("customer",),
        domains=("sales",),
        owners=("alice",),
        versions=("1.0.0",),
    ) == (item,)
    for status in ("imported", "validated", "published", "archived", "deleted"):
        item = platform.transition(item.id, status, scope)
    assert item.status.value == "deleted"
    with pytest.raises(PermissionError):
        platform.get_dataset(item.id, DataScope("tenant-b", "workspace-a"))


def test_pipeline_retry_checkpoint_lineage_and_metrics() -> None:
    platform = DataPlatform()
    scope = DataScope("tenant-a", "workspace-a")
    platform.create_dataset(payload())
    pipeline = platform.create_pipeline(
        {
            "id": "pipe-1",
            "name": "Publish customers",
            "tenant": "tenant-a",
            "workspace": "workspace-a",
            "source": "data-1",
            "target": "data-2",
            "transformations": ["normalize"],
            "schedule": "0 * * * *",
            "max_retries": 2,
        }
    )
    attempts = 0

    def operation() -> None:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise RuntimeError("retry")

    assert (
        platform.run_pipeline(pipeline.id, scope, operation).checkpoint == "attempt:2"
    )
    edge = LineageEdge("data-1", "data-2", "pipe-1", "normalize", ("crm",))
    platform.record_lineage(edge)
    assert platform.lineage_for("data-2") == (edge,)
    assert platform.metrics.snapshot()["pipelines_total"] == 1


def test_storage_connectors_schema_quality_import_export() -> None:
    store = ObjectStorage()
    store.put("key", b"value")
    assert store.get("key") == b"value"
    store.delete("key")
    platform = DataPlatform()
    scope = DataScope("tenant-a", "workspace-a")
    platform.create_dataset(payload())
    connector = MemoryConnector({"input": b"[]"})
    request = ConnectorRequest("input", 10)
    assert platform.import_data("data-1", scope, connector, request) == b"[]"
    platform.export_data(
        "data-1", scope, connector, ConnectorRequest("output", 10), b"ok"
    )
    result = platform.validate(
        "data-1",
        scope,
        ({"id": "1", "email": "a"}, {"id": "1"}),
        (QualityRule("unique-id", "uniqueness", "id", 1.0),),
    )
    assert not result.passed and set(result.failures) == {
        "unique-id",
        "schema-validation",
    }
    assert validate_schema(payload()["schema"], {"id": "1"}) == ("email",)  # type: ignore[arg-type]
    assert compatible(
        {"fields": {"id": "str"}}, {"fields": {"id": "str", "name": "str"}}
    )
    assert migrate({"old": 1}, {"old": "new"}, {"added": 2}) == {"new": 1, "added": 2}
    restricted = platform.create_dataset(
        payload(id="restricted", classification="restricted")
    )
    with pytest.raises(PermissionError):
        platform.export_data(
            restricted.id, scope, connector, ConnectorRequest("x"), b"x"
        )


class App:
    def __init__(self) -> None:
        self.routes: set[tuple[str, str]] = set()

    def add_api_route(
        self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        self.routes.update((method, path) for method in methods)


def test_api_dashboard_validation_and_regression_contract() -> None:
    app = App()
    platform = DataPlatform()
    register_data_routes(app, platform)
    for path in (
        "/data",
        "/datasets",
        "/pipelines",
        "/lineage",
        "/quality",
        "/classification",
    ):
        assert any(item[1] == path for item in app.routes)
    assert (
        platform.dashboard(DataScope("tenant-a", "workspace-a"))["sections"] == SECTIONS
    )
    assert set(platform.metrics.snapshot()) == {
        "datasets_total",
        "pipelines_total",
        "quality_failures_total",
        "imports_total",
        "exports_total",
    }
