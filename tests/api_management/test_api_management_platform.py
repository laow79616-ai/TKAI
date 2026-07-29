"""API management platform tests."""

import pytest

from api_management import (
    METRICS,
    ApiManagementPlatform,
    ApiScope,
    ApiStatus,
    ApiVersion,
    CachePolicy,
    Credential,
    Gateway,
    GatewayRequest,
    GatewayResponse,
    ManagedApi,
    Policy,
    Quota,
    RateLimit,
    Route,
    Subscription,
    SubscriptionStatus,
    Visibility,
)
from api_management.dashboard import SECTIONS


@pytest.fixture
def configured() -> tuple[ApiManagementPlatform, ApiScope]:
    platform = ApiManagementPlatform()
    scope = ApiScope(
        "tenant-a",
        "workspace-a",
        "operator",
        frozenset(
            {
                "api-management:read",
                "api-management:write",
                "api-management:publish",
                "api-management:policy",
                "api-management:credentials",
                "api-management:subscribe",
                "api-management:invoke",
            }
        ),
        frozenset({"inference:read"}),
        "app-a",
        "agent-a",
    )
    platform.create_api(
        ManagedApi(
            "inference",
            "Inference",
            "Enterprise model inference API",
            "ai-platform",
            scope.tenant,
            scope.workspace,
            "1.0.0",
            "/ai/v1",
            visibility=Visibility.INTERNAL,
            metadata={"openapi_reference": "https://docs.example/openapi.json"},
        ),
        scope,
    )
    platform.add_gateway(
        Gateway("gateway-a", "Primary", scope.tenant, scope.workspace), scope
    )
    platform.add_route(
        Route(
            "route-a",
            "inference",
            "gateway-a",
            "/generate",
            ("POST",),
            "service://model-runtime",
            scope.tenant,
            scope.workspace,
        ),
        scope,
    )
    platform.add_version(
        ApiVersion(
            "version-a",
            "inference",
            "1.0.0",
            scope.tenant,
            scope.workspace,
            active=True,
            default=True,
        ),
        scope,
    )
    platform.subscribe(
        Subscription(
            "subscription-a",
            "inference",
            "consumer-a",
            "app-a",
            "enterprise",
            frozenset({"inference"}),
            Quota(),
            scope.tenant,
            scope.workspace,
            SubscriptionStatus.ACTIVE,
        ),
        scope,
    )
    return platform, scope


def test_managed_api_lifecycle_isolation_versioning_and_dashboard(
    configured: tuple[ApiManagementPlatform, ApiScope],
) -> None:
    platform, scope = configured
    assert platform.list_apis(ApiScope("tenant-b", "workspace-a", "reader")) == []
    platform.set_status("inference", ApiStatus.PUBLISHED, scope)
    platform.set_status("inference", ApiStatus.DEPRECATED, scope)
    with pytest.raises(ValueError, match="Invalid lifecycle"):
        platform.set_status("inference", ApiStatus.DRAFT, scope)
    with pytest.raises(ValueError, match="semantic"):
        ManagedApi("bad", "Bad", "", "owner", "t", "w", "v1", "/bad")
    assert set(platform.dashboard(scope)) == set(SECTIONS)
    assert set(platform.metrics.snapshot()) == set(METRICS)


def test_gateway_policies_transform_cache_analytics_and_security(
    configured: tuple[ApiManagementPlatform, ApiScope],
) -> None:
    platform, scope = configured
    platform.set_status("inference", ApiStatus.PUBLISHED, scope)
    platform.add_policy(
        Policy(
            "scope-policy",
            "Inference Scope",
            "authorization",
            scope.tenant,
            scope.workspace,
            "inference",
            configuration={"scopes": ["inference:read"]},
        ),
        scope,
    )
    platform.add_policy(
        Policy(
            "headers",
            "Safe headers",
            "transformation",
            scope.tenant,
            scope.workspace,
            "inference",
            configuration={
                "request_headers": {"x-platform": "tkai"},
                "response_headers": {"x-api-version": "1"},
            },
        ),
        scope,
    )
    platform.add_cache_policy(
        CachePolicy("cache-a", "inference", scope.tenant, scope.workspace), scope
    )
    calls = 0

    def upstream(route: Route, request: GatewayRequest) -> GatewayResponse:
        nonlocal calls
        calls += 1
        assert route.upstream_reference == "service://model-runtime"
        assert request.headers["x-platform"] == "tkai"
        return GatewayResponse(200, {}, b'{"result":"ok"}')

    request = GatewayRequest(
        "/ai/v1/generate", "POST", {}, b"{}", "consumer-a", tokens=12
    )
    first = platform.proxy(request, scope, upstream)
    second = platform.proxy(request, scope, upstream)
    assert first == second
    assert first.headers["x-api-version"] == "1"
    assert calls == 1
    assert platform.analytics[0]["route_id"] == "route-a"
    assert "result" not in repr(platform.analytics)
    assert platform.invalidate_cache("inference", scope) == 1
    with pytest.raises(ValueError, match="arbitrary"):
        Policy(
            "unsafe",
            "Unsafe",
            "transformation",
            scope.tenant,
            scope.workspace,
            configuration={"code": "open('/etc/passwd')"},
        )


def test_authentication_rate_limit_quota_subscription_and_payload_bounds(
    configured: tuple[ApiManagementPlatform, ApiScope],
) -> None:
    platform, scope = configured
    with pytest.raises(ValueError, match="opaque"):
        Credential("bad", "api_key", "plaintext", "tenant-a", "workspace-a", "c")
    credential = platform.add_credential(
        Credential(
            "key-a",
            "api_key",
            "vault://api-management/key-a",
            scope.tenant,
            scope.workspace,
            "consumer-a",
        ),
        scope,
    )
    platform.rotate_credential(credential.id, scope)
    platform.revoke_credential(credential.id, scope)
    assert credential.rotated_at is not None and credential.revoked_at is not None
    assert "vault://api-management/key-a" not in repr(platform.audit)

    platform.set_status("inference", ApiStatus.PUBLISHED, scope)
    platform.set_rate_limit(
        "consumer:consumer-a",
        RateLimit(1, 2, 1, 1),
        scope,
    )
    platform.set_quota(
        "consumer:consumer-a",
        Quota(request_quota=2, token_quota=10, data_transfer_bytes=100),
        scope,
    )
    request = GatewayRequest("/ai/v1/generate", "POST", {}, b"{}", "consumer-a", 5)

    def upstream(route: Route, item: GatewayRequest) -> GatewayResponse:
        return GatewayResponse(200, {}, b"ok")

    platform.proxy(request, scope, upstream)
    platform.proxy(request, scope, upstream)
    with pytest.raises(RuntimeError, match="Rate limit|Quota"):
        platform.proxy(request, scope, upstream)
    assert (
        platform.metrics.snapshot()["api_rate_limit_rejections_total"]
        + platform.metrics.snapshot()["api_quota_rejections_total"]
        == 1
    )
    oversized = GatewayRequest(
        "/ai/v1/generate", "POST", {}, b"x" * 1_048_577, "consumer-a"
    )
    with pytest.raises(ValueError, match="payload"):
        platform.proxy(oversized, scope, upstream)


def test_portal_visibility_and_rbac(
    configured: tuple[ApiManagementPlatform, ApiScope],
) -> None:
    platform, scope = configured
    platform.set_status("inference", ApiStatus.PUBLISHED, scope)
    portal = platform.developer_portal(scope)
    assert portal["catalog"][0]["id"] == "inference"
    assert portal["credentials"] == {"interface": "secret-reference-only"}
    with pytest.raises(PermissionError, match="RBAC"):
        platform.create_api(
            ManagedApi("x", "X", "", "owner", "tenant-a", "workspace-a", "1.0.0", "/x"),
            ApiScope("tenant-a", "workspace-a", "viewer"),
        )
