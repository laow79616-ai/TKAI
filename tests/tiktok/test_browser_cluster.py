from __future__ import annotations

import pytest

from tiktok.browser_cluster import (
    BrowserCluster,
    BrowserProfileTemplate,
    ClusterBrowserInstance,
    ClusterNode,
    ClusterScope,
    ClusterStatus,
    InstanceStatus,
    ResourcePolicy,
    TikTokBrowserCluster,
)
from tiktok.browser_cluster.api import ROUTES, register_browser_cluster_routes
from tiktok.browser_cluster.metrics import METRIC_NAMES


def scope(workspace: str = "workspace-a") -> ClusterScope:
    return ClusterScope(
        "tenant-a",
        workspace,
        "operator",
        frozenset({"tiktok:browser-cluster:admin"}),
    )


def configured_cluster(**kwargs: object) -> TikTokBrowserCluster:
    service = TikTokBrowserCluster(**kwargs)
    service.create_cluster(
        BrowserCluster(
            "cluster-1", "Local", "Test", "tenant-a", "workspace-a", "owner"
        ),
        scope(),
    )
    service.transition("cluster-1", ClusterStatus.READY, scope())
    service.transition("cluster-1", ClusterStatus.RUNNING, scope())
    service.register_node(
        ClusterNode(
            "node-1",
            "cluster-1",
            "tenant-a",
            "workspace-a",
            "localhost",
            4,
            4.0,
            4096,
            4,
        ),
        scope(),
    )
    return service


def instance(identifier: str, account: str = "account-1") -> ClusterBrowserInstance:
    return ClusterBrowserInstance(
        identifier,
        "cluster-1",
        "tenant-a",
        "workspace-a",
        f"browser-runtime://{identifier}",
        "profile-default",
        account,
        cpu_reservation=0.5,
        memory_reservation_mb=256,
    )


def test_lifecycle_node_scheduling_resources_health_and_statistics() -> None:
    service = configured_cluster(
        resources=ResourcePolicy(maximum_parallel_launches=2, account_limit=1)
    )
    service.create_instance(instance("browser-1"), scope())
    service.create_instance(instance("browser-2", "account-2"), scope())
    service.enqueue("browser-1", scope(), priority=1)
    service.enqueue("browser-2", scope(), priority=2)
    assert service.process_queue(scope()) == ["browser-2", "browser-1"]
    assert service.instances["browser-1"].status is InstanceStatus.RUNNING
    assert service.nodes["node-1"].running_browsers == 2
    assert service.health(scope())["score"] == 100.0
    assert service.statistics(scope())["running_browsers"] == 2
    service.release("browser-1", scope())
    assert service.nodes["node-1"].running_browsers == 1


def test_workspace_isolation_and_bounded_account_queue() -> None:
    service = configured_cluster()
    service.create_instance(instance("browser-1"), scope())
    service.create_instance(instance("browser-2"), scope())
    service.enqueue("browser-1", scope())
    service.enqueue("browser-2", scope())
    assert service.process_queue(scope()) == ["browser-1"]
    with pytest.raises(PermissionError):
        service.enqueue("browser-2", scope("workspace-b"))


class RestrictedRisk:
    def has_unresolved_restriction(
        self, tenant: str, workspace: str, account_reference: str
    ) -> bool:
        return True


def test_recovery_stops_for_unresolved_tiktok_restriction() -> None:
    service = configured_cluster(risk_control=RestrictedRisk())
    service.create_instance(instance("browser-1"), scope())
    record = service.recover("browser-1", scope(), reason="challenge")
    assert record.stopped_for_restriction
    assert not record.recovered
    assert service.instances["browser-1"].status is InstanceStatus.PAUSED


def test_metrics_api_dashboard_and_secret_redaction() -> None:
    service = TikTokBrowserCluster()
    cluster = BrowserCluster(
        "cluster-1",
        "Local",
        "Test",
        "tenant-a",
        "workspace-a",
        "owner",
        metadata={"token": "unsafe", "region": "local"},
    )
    service.create_cluster(cluster, scope())
    service.create_profile(
        BrowserProfileTemplate(
            "default",
            "tenant-a",
            "workspace-a",
            "Default",
            1,
            settings={"locale_reference": "profile://locale/en-US"},
        ),
        scope(),
    )
    assert cluster.metadata == {"region": "local"}
    assert set(METRIC_NAMES) == set(service.metrics.values)
    assert "Cluster Overview" in service.dashboard(scope())["sections"]
    assert service.dashboard(scope())["queues"]["maximum_parallel_launches"] == 4

    class App:
        def __init__(self) -> None:
            self.paths: list[str] = []

        def add_api_route(self, path: str, handler: object, methods: list[str]) -> None:
            self.paths.append(path)

    app = App()
    register_browser_cluster_routes(app, service)
    assert tuple(app.paths) == ROUTES
