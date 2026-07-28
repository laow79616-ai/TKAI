import pytest

from business_intelligence import (
    Aggregation,
    BIQuery,
    BIScope,
    BIWorkspace,
    BusinessIntelligencePlatform,
    Dataset,
    DataSource,
    DataSourceType,
    ExportFormat,
    ExportRequest,
    Measure,
    Metric,
    Visibility,
    WorkspaceStatus,
)


@pytest.fixture
def system() -> tuple[BusinessIntelligencePlatform, BIScope]:
    platform = BusinessIntelligencePlatform(max_rows=1000)
    scope = BIScope(
        "tenant-a",
        "workspace-a",
        "owner",
        frozenset({"business_intelligence:admin"}),
    )
    platform.create_workspace(
        BIWorkspace(
            "bi-1",
            "Executive BI",
            "Governed analytics",
            scope.tenant,
            scope.workspace,
            scope.actor,
            visibility=Visibility.WORKSPACE,
        ),
        scope,
    )
    platform.add_data_source(
        DataSource(
            "source-1",
            scope.tenant,
            scope.workspace,
            "Warehouse",
            DataSourceType.WAREHOUSE,
            "warehouse://analytics",
            "vault://bi/warehouse",
        ),
        scope,
    )
    platform.add_dataset(
        Dataset(
            "dataset-1",
            scope.tenant,
            scope.workspace,
            "Sales",
            "source-1",
            {"sales": {"type": "number"}},
        ),
        scope,
    )
    return platform, scope


def test_workspace_lifecycle_and_isolation(
    system: tuple[BusinessIntelligencePlatform, BIScope],
) -> None:
    platform, scope = system
    for status in (
        WorkspaceStatus.ACTIVE,
        WorkspaceStatus.PAUSED,
        WorkspaceStatus.ACTIVE,
        WorkspaceStatus.ARCHIVED,
        WorkspaceStatus.DELETED,
    ):
        assert platform.set_workspace_status("bi-1", status, scope).status is status
    other = BIScope(
        "tenant-b",
        scope.workspace,
        "attacker",
        frozenset({"business_intelligence:admin"}),
    )
    assert platform.resource("workspaces", other) == []
    assert platform.audit


def test_bounded_metrics_measures_queries_and_exports(
    system: tuple[BusinessIntelligencePlatform, BIScope],
) -> None:
    platform, scope = system
    platform.add_metric(
        Metric(
            "metric-1",
            scope.tenant,
            scope.workspace,
            "Revenue",
            "Total revenue",
            "SUM(revenue)",
            Aggregation.SUM,
            "USD",
            scope.actor,
        ),
        scope,
    )
    platform.add_measure(
        Measure(
            "measure-1",
            scope.tenant,
            scope.workspace,
            "Margin",
            Aggregation.RATIO,
            "profit / revenue",
        ),
        scope,
    )
    result = platform.execute_query(
        BIQuery(
            "query-1",
            scope.tenant,
            scope.workspace,
            "dataset-1",
            metrics=("Revenue",),
            row_limit=100,
        ),
        scope,
    )
    assert result["row_count"] == 0
    platform.request_export(
        ExportRequest(
            "export-1",
            scope.tenant,
            scope.workspace,
            "report",
            "report-1",
            ExportFormat.CSV,
            row_limit=100,
        ),
        scope,
    )
    snapshot = platform.metrics.snapshot()
    assert snapshot["bi_queries_total"] == 1
    assert snapshot["bi_exports_total"] == 1
    with pytest.raises(ValueError, match="prohibited"):
        platform.add_measure(
            Measure(
                "bad",
                scope.tenant,
                scope.workspace,
                "Bad",
                Aggregation.CUSTOM,
                "value; DROP TABLE facts",
            ),
            scope,
        )
    with pytest.raises(ValueError, match="row limit"):
        platform.execute_query(
            BIQuery(
                "too-large",
                scope.tenant,
                scope.workspace,
                "dataset-1",
                row_limit=1001,
            ),
            scope,
        )


def test_plaintext_credential_and_secret_metadata_are_rejected(
    system: tuple[BusinessIntelligencePlatform, BIScope],
) -> None:
    platform, scope = system
    with pytest.raises(ValueError, match="credential reference"):
        platform.add_data_source(
            DataSource(
                "bad",
                scope.tenant,
                scope.workspace,
                "Unsafe",
                DataSourceType.DATABASE,
                "database://unsafe",
                "password=plaintext",
            ),
            scope,
        )
    with pytest.raises(ValueError, match="Secrets"):
        platform.create_workspace(
            BIWorkspace(
                "bad",
                "Unsafe",
                "",
                scope.tenant,
                scope.workspace,
                scope.actor,
                metadata={"api_token": "secret"},
            ),
            scope,
        )
