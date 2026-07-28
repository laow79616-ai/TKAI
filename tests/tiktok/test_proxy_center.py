from __future__ import annotations

from dataclasses import asdict

import pytest

from tiktok.proxy_center import (
    METRICS,
    BindingTarget,
    BrowserRuntimeProxyAdapter,
    GroupType,
    Proxy,
    ProxyBinding,
    ProxyGroup,
    ProxyProtocol,
    ProxyScope,
    ProxyStatus,
    ProxyType,
    ProxyVerifier,
    ReferenceSecretResolver,
    RotationMode,
    RotationPolicy,
    TikTokProxyCenter,
)


class VerificationDouble:
    def resolve(self, host: str) -> bool:
        return host == "proxy.local"

    def tcp(self, host: str, port: int, timeout: float) -> bool:
        return host == "proxy.local" and port == 8443 and timeout <= 3

    def tls(self, host: str, port: int, timeout: float) -> bool:
        return True

    def public_ip(self, proxy: Proxy, timeout: float) -> tuple[bool, str]:
        return True, "203.0.113.10"

    def geo(self, public_ip: str, country: str, region: str) -> bool:
        return public_ip == "203.0.113.10" and country == "US"

    def authenticate(self, proxy: Proxy) -> bool:
        return proxy.credential_reference == "vault://proxy/1"


@pytest.fixture
def scope() -> ProxyScope:
    return ProxyScope(
        "tenant-a",
        "workspace-a",
        "operator",
        frozenset(
            {
                "tiktok:proxy:read",
                "tiktok:proxy:write",
                "tiktok:proxy:verify",
                "tiktok:proxy:rotate",
                "tiktok:proxy:bind",
                "tiktok:proxy:acquire",
                "tiktok:proxy:release",
                "tiktok:proxy:admin",
            }
        ),
    )


@pytest.fixture
def center() -> TikTokProxyCenter:
    secrets = ReferenceSecretResolver({("tenant-a", "workspace-a", "vault://proxy/1")})
    return TikTokProxyCenter(
        secret_resolver=secrets,
        verifier=ProxyVerifier(VerificationDouble()),
        maximum_pool_size=5,
        maximum_concurrency=2,
        maximum_queue_size=4,
    )


def make_proxy(identifier: str = "proxy-1", *, country: str = "US") -> Proxy:
    return Proxy(
        identifier,
        f"Proxy {identifier}",
        "tenant-a",
        "workspace-a",
        ProxyType.IPV4,
        ProxyProtocol.HTTPS,
        "proxy.local",
        8443,
        "vault://proxy/1",
        "provider-ref",
        "us-east",
        country,
        "isp-ref",
        metadata={"classification": "residential"},
    )


def available(center: TikTokProxyCenter, scope: ProxyScope, identifier: str) -> Proxy:
    proxy = center.create(make_proxy(identifier), scope)
    return center.transition(proxy.id, ProxyStatus.AVAILABLE, scope)


def test_crud_lifecycle_security_and_isolation(center, scope):
    proxy = center.create(make_proxy(), scope)
    assert proxy.to_dict()["credential_reference"] == "vault://proxy/1"
    assert center.update(proxy.id, scope, name="Renamed").name == "Renamed"
    center.transition(proxy.id, ProxyStatus.AVAILABLE, scope)
    center.transition(proxy.id, ProxyStatus.DISABLED, scope)
    center.transition(proxy.id, ProxyStatus.ARCHIVED, scope)
    assert center.delete(proxy.id, scope).status is ProxyStatus.DELETED
    assert center.list(scope) == []
    assert center.list(scope, include_deleted=True) == [proxy]

    other = ProxyScope("tenant-a", "workspace-b", "intruder")
    assert center.list(other) == []
    with pytest.raises(PermissionError):
        center.get(proxy.id, other)
    with pytest.raises(ValueError):
        center.create(
            Proxy(
                "bad",
                "Bad",
                scope.tenant,
                scope.workspace,
                ProxyType.IPV4,
                ProxyProtocol.HTTP,
                "user:password@proxy.local",
                80,
            ),
            scope,
        )


def test_verification_health_statistics_and_metrics(center, scope):
    proxy = available(center, scope, "verified")
    result = center.verify(proxy.id, scope)
    assert result.successful and result.public_ip == "203.0.113.10"
    assert center.health[proxy.id].health_score == 100
    center.record_usage(proxy.id, scope, successful=True, latency_seconds=0.2)
    center.record_usage(proxy.id, scope, successful=False, latency_seconds=0.4)
    stats = center.statistics(scope)
    assert stats["usage"] == 2
    assert stats["success"] == stats["failure"] == 1
    assert stats["average_latency"] == pytest.approx(0.3)
    assert set(center.metrics.snapshot()) == set(METRICS)
    assert "tiktok_proxy_latency_seconds" in center.metrics.render_prometheus()


def test_groups_bindings_pool_rotation_and_browser_adapter(center, scope):
    first = available(center, scope, "proxy-a")
    second = available(center, scope, "proxy-b")
    center.create_group(
        ProxyGroup(
            "group-1",
            "Residential US",
            scope.tenant,
            scope.workspace,
            GroupType.RESIDENTIAL,
            {first.id, second.id},
        ),
        scope,
    )
    center.create_binding(
        ProxyBinding(
            "binding-1",
            scope.tenant,
            scope.workspace,
            BindingTarget.BROWSER_RUNTIME,
            "browser-1",
            group_reference="group-1",
            priority=10,
            affinity="us-east",
            sticky_session_reference="sticky://1",
        ),
        scope,
    )
    center.create_rotation_policy(
        RotationPolicy(
            "rotation-1",
            scope.tenant,
            scope.workspace,
            RotationMode.FAILURE_TRIGGER,
            group_reference="group-1",
        ),
        scope,
    )
    allocation = center.acquire(
        scope,
        target_type=BindingTarget.BROWSER_RUNTIME,
        target_reference="browser-1",
        country="US",
    )
    rotated = center.rotate(allocation.id, scope, reason="failure")
    assert rotated.proxy_id != allocation.proxy_id
    center.release(rotated.id, scope)

    adapter = BrowserRuntimeProxyAdapter(center)
    endpoint = adapter.acquire_for_launch(
        scope, browser_reference="browser-1", country="US"
    )
    assert endpoint.credential_reference == "vault://proxy/1"
    adapter.release_from_launch(endpoint.proxy_id, "browser-1", scope)


def test_scheduler_priority_fairness_retry_and_bounds(center, scope):
    available(center, scope, "scheduled")
    low = center.enqueue(scope, BindingTarget.WORKSPACE, scope.workspace, priority=1)
    high = center.enqueue(scope, BindingTarget.PROJECT, "project-1", priority=10)
    allocation = center.schedule_next(scope)
    assert allocation is not None
    assert allocation.target_reference == high.target_reference
    center.release(allocation.id, scope)
    assert center.schedule_next(scope).target_reference == low.target_reference

    with pytest.raises(ValueError):
        center.enqueue(
            scope,
            BindingTarget.WORKSPACE,
            scope.workspace,
            timeout_seconds=100,
        )


def test_pool_reserve_recycle_drain_dashboard_and_audit(center, scope):
    proxy = available(center, scope, "pool")
    allocation = center.acquire(
        scope,
        target_type=BindingTarget.AUTOMATION_WORKFLOW,
        target_reference="workflow-1",
        reserve=True,
    )
    assert allocation.reserved
    center.release(allocation.id, scope)
    proxy.status = ProxyStatus.COOLING
    assert center.recycle(proxy.id, scope).status is ProxyStatus.AVAILABLE
    assert center.drain(scope) == 1
    dashboard = center.dashboard(scope)
    assert dashboard["sections"][0] == "Proxy Inventory"
    assert dashboard["proxy_inventory"] == 1
    assert center.audit and "password" not in str(center.audit).casefold()


def test_api_dashboard_and_route_contract(center):
    from tiktok.proxy_center.api import ROUTES, register_proxy_center_routes

    class App:
        def __init__(self):
            self.routes = []

        def add_api_route(self, path, endpoint, methods, tags):
            self.routes.append((path, tuple(methods), endpoint, tuple(tags)))

    app = App()
    register_proxy_center_routes(app, center)
    paths = {path for path, _, _, _ in app.routes}
    assert set(ROUTES) <= paths
    assert {
        "/tiktok/proxy-center/dashboard",
        "/tiktok/proxy-center/metrics",
    } <= paths


def test_no_social_platform_modules_or_plaintext_credentials():
    proxy = make_proxy()
    serialized = asdict(proxy)
    assert "username" not in serialized and "password" not in serialized
    for forbidden in ("telegram", "whatsapp", "facebook", "instagram", "discord"):
        assert forbidden not in str(serialized).casefold()
