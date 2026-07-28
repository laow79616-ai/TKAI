"""Secure, tenant-scoped Enterprise AI API Management control plane."""

from __future__ import annotations

import hashlib
import re
import secrets
from collections import defaultdict, deque
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from time import monotonic
from typing import Any, Protocol

from .metrics import ApiManagementMetrics


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ApiStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    SUSPENDED = "suspended"
    RETIRED = "retired"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Visibility(str, Enum):
    PRIVATE = "private"
    INTERNAL = "internal"
    PARTNER = "partner"
    PUBLIC = "public"


class SubscriptionStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class ApiScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"api-management:read"})
    scopes: frozenset[str] = frozenset()
    application: str | None = None
    agent: str | None = None

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class ManagedApi:
    id: str
    name: str
    description: str
    owner: str
    tenant: str
    workspace: str
    version: str
    base_path: str
    status: ApiStatus = ApiStatus.DRAFT
    visibility: Visibility = Visibility.PRIVATE
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.base_path.startswith("/") or ".." in self.base_path:
            raise ValueError("Base path must be an absolute normalized path.")
        _semantic_version(self.version)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["visibility"] = self.visibility.value
        return value


@dataclass(slots=True)
class Gateway:
    id: str
    name: str
    tenant: str
    workspace: str
    health_check: str = "/health"
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Route:
    id: str
    api_id: str
    gateway_id: str
    path: str
    methods: tuple[str, ...]
    upstream_reference: str
    tenant: str
    workspace: str
    load_balancing: str = "round_robin"
    timeout_seconds: float = 30
    retry_attempts: int = 2
    circuit_breaker: str = "default"
    health_check: str = "/health"
    max_request_bytes: int = 1_048_576
    max_response_bytes: int = 5_242_880

    def __post_init__(self) -> None:
        if not self.path.startswith("/") or not self.upstream_reference.startswith(
            ("service://", "https://")
        ):
            raise ValueError("Route path or upstream reference is invalid.")
        if not 0 < self.timeout_seconds <= 300 or not 0 <= self.retry_attempts <= 10:
            raise ValueError("Timeout and retry values must be bounded.")
        if not 1 <= self.max_request_bytes <= 10_485_760:
            raise ValueError("Request size must be between 1 byte and 10 MiB.")
        if not 1 <= self.max_response_bytes <= 52_428_800:
            raise ValueError("Response size must be between 1 byte and 50 MiB.")
        self.methods = tuple(method.upper() for method in self.methods)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ApiVersion:
    id: str
    api_id: str
    semantic_version: str
    tenant: str
    workspace: str
    active: bool = False
    default: bool = False
    deprecation_date: datetime | None = None
    compatibility: str = "backward-compatible"
    migration_notes: str = ""

    def __post_init__(self) -> None:
        _semantic_version(self.semantic_version)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["deprecation_date"] = (
            self.deprecation_date.isoformat() if self.deprecation_date else None
        )
        return value


@dataclass(frozen=True, slots=True)
class RateLimit:
    requests_per_second: int = 10
    requests_per_minute: int = 600
    burst: int = 20
    concurrency: int = 10

    def __post_init__(self) -> None:
        values = (
            self.requests_per_second,
            self.requests_per_minute,
            self.burst,
            self.concurrency,
        )
        if any(value < 1 or value > 1_000_000 for value in values):
            raise ValueError("Rate-limit values must be between 1 and 1,000,000.")


@dataclass(frozen=True, slots=True)
class Quota:
    request_quota: int = 10_000
    token_quota: int = 1_000_000
    data_transfer_bytes: int = 1_073_741_824
    period: str = "monthly"

    def __post_init__(self) -> None:
        if self.period not in {"daily", "monthly", "subscription"}:
            raise ValueError("Quota period must be daily, monthly, or subscription.")
        if min(self.request_quota, self.token_quota, self.data_transfer_bytes) < 1:
            raise ValueError("Quota values must be positive.")


@dataclass(slots=True)
class Policy:
    id: str
    name: str
    kind: str
    tenant: str
    workspace: str
    api_id: str | None = None
    route_id: str | None = None
    configuration: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    ALLOWED_KINDS = frozenset(
        {
            "authentication",
            "authorization",
            "rate_limit",
            "quota",
            "cors",
            "header",
            "caching",
            "transformation",
            "ip_allowlist",
            "audit",
        }
    )

    def __post_init__(self) -> None:
        if self.kind not in self.ALLOWED_KINDS:
            raise ValueError("Unsupported policy kind.")
        if self.kind == "transformation" and any(
            key in self.configuration for key in ("code", "script", "command", "eval")
        ):
            raise ValueError("Transformation policies cannot execute arbitrary code.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Credential:
    id: str
    kind: str
    secret_reference: str
    tenant: str
    workspace: str
    consumer: str
    scopes: frozenset[str] = frozenset()
    revoked_at: datetime | None = None
    rotated_at: datetime | None = None

    def __post_init__(self) -> None:
        allowed = {"api_key", "bearer", "oauth2", "oidc", "service_token", "mtls"}
        if self.kind not in allowed:
            raise ValueError("Unsupported credential kind.")
        if not self.secret_reference.startswith(("secret://", "vault://", "kms://")):
            raise ValueError("Credentials must be opaque secret references.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "secret_reference": self.secret_reference,
            "tenant": self.tenant,
            "workspace": self.workspace,
            "consumer": self.consumer,
            "scopes": sorted(self.scopes),
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "rotated_at": self.rotated_at.isoformat() if self.rotated_at else None,
        }


@dataclass(slots=True)
class CachePolicy:
    id: str
    api_id: str
    tenant: str
    workspace: str
    ttl_seconds: int = 60
    key_fields: tuple[str, ...] = ("path",)
    max_entries: int = 1000
    exclude_sensitive: bool = True

    def __post_init__(self) -> None:
        if not 1 <= self.ttl_seconds <= 86_400 or not 1 <= self.max_entries <= 100_000:
            raise ValueError("Cache TTL or size is outside the bounded range.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Subscription:
    id: str
    api_id: str
    consumer: str
    application: str
    plan: str
    entitlements: frozenset[str]
    quota: Quota
    tenant: str
    workspace: str
    status: SubscriptionStatus = SubscriptionStatus.PENDING
    expiration: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["entitlements"] = sorted(self.entitlements)
        value["expiration"] = self.expiration.isoformat() if self.expiration else None
        return value


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: str
    actor: str
    tenant: str
    workspace: str
    occurred_at: datetime
    metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class GatewayRequest:
    path: str
    method: str
    headers: Mapping[str, str]
    body: bytes
    consumer: str
    tokens: int = 0


@dataclass(frozen=True, slots=True)
class GatewayResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes


class UpstreamHandler(Protocol):
    def __call__(self, route: Route, request: GatewayRequest) -> GatewayResponse: ...


def _semantic_version(value: str) -> None:
    if re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", value) is None:
        raise ValueError("Version must use semantic versioning (major.minor.patch).")


class ApiManagementPlatform:
    """In-memory reference control plane and safe gateway enforcement layer."""

    TRANSITIONS = {
        ApiStatus.DRAFT: {ApiStatus.PUBLISHED, ApiStatus.ARCHIVED, ApiStatus.DELETED},
        ApiStatus.PUBLISHED: {
            ApiStatus.DEPRECATED,
            ApiStatus.SUSPENDED,
            ApiStatus.RETIRED,
        },
        ApiStatus.DEPRECATED: {
            ApiStatus.SUSPENDED,
            ApiStatus.RETIRED,
            ApiStatus.ARCHIVED,
        },
        ApiStatus.SUSPENDED: {ApiStatus.PUBLISHED, ApiStatus.RETIRED},
        ApiStatus.RETIRED: {ApiStatus.ARCHIVED},
        ApiStatus.ARCHIVED: {ApiStatus.DELETED},
        ApiStatus.DELETED: set(),
    }

    def __init__(self) -> None:
        self.apis: dict[str, ManagedApi] = {}
        self.gateways: dict[str, Gateway] = {}
        self.routes: dict[str, Route] = {}
        self.versions: dict[str, ApiVersion] = {}
        self.policies: dict[str, Policy] = {}
        self.credentials: dict[str, Credential] = {}
        self.rate_limits: dict[str, RateLimit] = {}
        self.quotas: dict[str, Quota] = {}
        self.caches: dict[str, CachePolicy] = {}
        self.subscriptions: dict[str, Subscription] = {}
        self.audit: list[AuditEntry] = []
        self.analytics: list[dict[str, Any]] = []
        self.metrics = ApiManagementMetrics()
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._usage: dict[str, dict[str, int]] = defaultdict(
            lambda: {"requests": 0, "tokens": 0, "bytes": 0}
        )
        self._cache: dict[str, tuple[float, GatewayResponse]] = {}
        self._lock = Lock()

    @staticmethod
    def _check(record: Any, scope: ApiScope) -> None:
        if record.tenant != scope.tenant or record.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    @staticmethod
    def _require(scope: ApiScope, permission: str) -> None:
        if (
            permission not in scope.permissions
            and "api-management:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    def _audit(self, action: str, scope: ApiScope, **metadata: Any) -> None:
        safe = {key: value for key, value in metadata.items() if "secret" not in key}
        self.audit.append(
            AuditEntry(
                action, scope.actor, scope.tenant, scope.workspace, utcnow(), safe
            )
        )

    def _scoped(self, values: Any, scope: ApiScope) -> list[Any]:
        self._require(scope, "api-management:read")
        return [
            value
            for value in values
            if value.tenant == scope.tenant and value.workspace == scope.workspace
        ]

    def create_api(self, api: ManagedApi, scope: ApiScope) -> ManagedApi:
        self._require(scope, "api-management:write")
        self._check(api, scope)
        if api.id in self.apis:
            raise ValueError("Managed API already exists.")
        self.apis[api.id] = api
        self.metrics.increment("managed_apis_total")
        self._audit("api.create", scope, api_id=api.id)
        return api

    def list_apis(self, scope: ApiScope) -> list[ManagedApi]:
        return self._scoped(self.apis.values(), scope)

    def set_status(self, api_id: str, status: ApiStatus, scope: ApiScope) -> ManagedApi:
        self._require(scope, "api-management:publish")
        api = self.apis[api_id]
        self._check(api, scope)
        if status not in self.TRANSITIONS[api.status]:
            raise ValueError(
                f"Invalid lifecycle transition: {api.status.value} -> {status.value}"
            )
        api.status = status
        self._audit("api.status", scope, api_id=api_id, status=status.value)
        return api

    def add_gateway(self, gateway: Gateway, scope: ApiScope) -> Gateway:
        self._require(scope, "api-management:write")
        self._check(gateway, scope)
        self.gateways[gateway.id] = gateway
        return gateway

    def add_route(self, route: Route, scope: ApiScope) -> Route:
        self._require(scope, "api-management:write")
        self._check(route, scope)
        self._check(self.apis[route.api_id], scope)
        self._check(self.gateways[route.gateway_id], scope)
        self.routes[route.id] = route
        self._audit("route.create", scope, route_id=route.id)
        return route

    def add_version(self, version: ApiVersion, scope: ApiScope) -> ApiVersion:
        self._require(scope, "api-management:write")
        self._check(version, scope)
        self._check(self.apis[version.api_id], scope)
        if version.default:
            for current in self.versions.values():
                if current.api_id == version.api_id:
                    current.default = False
        self.versions[version.id] = version
        return version

    def add_policy(self, policy: Policy, scope: ApiScope) -> Policy:
        self._require(scope, "api-management:policy")
        self._check(policy, scope)
        self.policies[policy.id] = policy
        return policy

    def add_credential(self, credential: Credential, scope: ApiScope) -> Credential:
        self._require(scope, "api-management:credentials")
        self._check(credential, scope)
        self.credentials[credential.id] = credential
        self._audit("credential.create", scope, credential_id=credential.id)
        return credential

    def revoke_credential(self, credential_id: str, scope: ApiScope) -> None:
        self._require(scope, "api-management:credentials")
        credential = self.credentials[credential_id]
        self._check(credential, scope)
        credential.revoked_at = utcnow()
        self._audit("credential.revoke", scope, credential_id=credential_id)

    def rotate_credential(self, credential_id: str, scope: ApiScope) -> None:
        self._require(scope, "api-management:credentials")
        credential = self.credentials[credential_id]
        self._check(credential, scope)
        credential.rotated_at = utcnow()
        self._audit("credential.rotate", scope, credential_id=credential_id)

    def set_rate_limit(
        self, target: str, limit: RateLimit, scope: ApiScope
    ) -> RateLimit:
        self._require(scope, "api-management:policy")
        self.rate_limits[self._key(target, scope)] = limit
        return limit

    def set_quota(self, target: str, quota: Quota, scope: ApiScope) -> Quota:
        self._require(scope, "api-management:policy")
        self.quotas[self._key(target, scope)] = quota
        return quota

    def add_cache_policy(self, policy: CachePolicy, scope: ApiScope) -> CachePolicy:
        self._require(scope, "api-management:policy")
        self._check(policy, scope)
        self.caches[policy.api_id] = policy
        return policy

    def invalidate_cache(self, api_id: str, scope: ApiScope) -> int:
        self._require(scope, "api-management:write")
        self._check(self.apis[api_id], scope)
        keys = [key for key in self._cache if key.startswith(f"{api_id}:")]
        for key in keys:
            del self._cache[key]
        return len(keys)

    def subscribe(
        self, subscription: Subscription, scope: ApiScope
    ) -> Subscription:
        self._require(scope, "api-management:subscribe")
        self._check(subscription, scope)
        self._check(self.apis[subscription.api_id], scope)
        self.subscriptions[subscription.id] = subscription
        self.metrics.increment("api_subscriptions_total")
        self._update_consumers()
        return subscription

    def activate_subscription(self, subscription_id: str, scope: ApiScope) -> None:
        self._require(scope, "api-management:write")
        subscription = self.subscriptions[subscription_id]
        self._check(subscription, scope)
        subscription.status = SubscriptionStatus.ACTIVE
        self._update_consumers()

    def match_route(
        self, path: str, method: str, scope: ApiScope
    ) -> tuple[ManagedApi, Route]:
        candidates: list[tuple[int, ManagedApi, Route]] = []
        for route in self._scoped(self.routes.values(), scope):
            api = self.apis[route.api_id]
            full_path = api.base_path.rstrip("/") + route.path
            if path.startswith(full_path) and method.upper() in route.methods:
                candidates.append((len(full_path), api, route))
        if not candidates:
            raise LookupError("No matching API route.")
        _, api, route = max(candidates, key=lambda item: item[0])
        return api, route

    def proxy(
        self,
        request: GatewayRequest,
        scope: ApiScope,
        upstream: UpstreamHandler,
    ) -> GatewayResponse:
        self._require(scope, "api-management:invoke")
        started = monotonic()
        self.metrics.increment("api_gateway_requests_total")
        try:
            api, route = self.match_route(request.path, request.method, scope)
            if api.status is not ApiStatus.PUBLISHED:
                raise PermissionError("API is not published.")
            if len(request.body) > route.max_request_bytes:
                raise ValueError("Request exceeds the configured payload bound.")
            self._authorize(api, route, request, scope)
            self._enforce_rate_limit(api, route, request, scope)
            self._enforce_quota(api, request, scope)
            cache_key = self._cache_key(api, request)
            cached = self._cache.get(cache_key)
            if cached and cached[0] > monotonic():
                return cached[1]
            response = upstream(route, self._transform_request(request, api, route))
            if len(response.body) > route.max_response_bytes:
                raise ValueError("Response exceeds the configured payload bound.")
            response = self._transform_response(response, api, route)
            self._record(api, route, request, response.status_code, started)
            self._cache_response(api, cache_key, response)
            return response
        except Exception:
            self.metrics.increment("api_gateway_failures_total")
            raise
        finally:
            self.metrics.increment("api_gateway_latency_seconds", monotonic() - started)

    def developer_portal(self, scope: ApiScope) -> dict[str, Any]:
        apis = self.list_apis(scope)
        catalog = [
            api.to_dict()
            for api in apis
            if api.status in {ApiStatus.PUBLISHED, ApiStatus.DEPRECATED}
            and api.visibility is not Visibility.PRIVATE
        ]
        subscriptions = [
            item.to_dict() for item in self._scoped(self.subscriptions.values(), scope)
        ]
        return {
            "catalog": catalog,
            "documentation": "OpenAPI references are exposed through API metadata.",
            "openapi": [api.metadata.get("openapi_reference") for api in apis],
            "credentials": {"interface": "secret-reference-only"},
            "subscriptions": subscriptions,
            "usage": dict(self._usage),
            "examples": [api.metadata.get("example") for api in apis],
        }

    def dashboard(self, scope: ApiScope) -> dict[str, Any]:
        collections = {
            "apis": self.apis.values(),
            "gateways": self.gateways.values(),
            "routes": self.routes.values(),
            "versions": self.versions.values(),
            "policies": self.policies.values(),
            "credentials": self.credentials.values(),
            "subscriptions": self.subscriptions.values(),
        }
        result: dict[str, Any] = {
            name: [item.to_dict() for item in self._scoped(values, scope)]
            for name, values in collections.items()
        }
        result["rate_limits"] = self._configuration(self.rate_limits, scope)
        result["quotas"] = self._configuration(self.quotas, scope)
        result["analytics"] = [
            item
            for item in self.analytics
            if item["tenant"] == scope.tenant and item["workspace"] == scope.workspace
        ]
        result["developer_portal"] = self.developer_portal(scope)
        result["metrics"] = self.metrics.snapshot()
        return result

    def _authorize(
        self, api: ManagedApi, route: Route, request: GatewayRequest, scope: ApiScope
    ) -> None:
        subscription = next(
            (
                item
                for item in self.subscriptions.values()
                if item.api_id == api.id
                and item.consumer == request.consumer
                and item.tenant == scope.tenant
                and item.workspace == scope.workspace
                and item.status is SubscriptionStatus.ACTIVE
                and (item.expiration is None or item.expiration > utcnow())
            ),
            None,
        )
        if api.visibility is not Visibility.PUBLIC and subscription is None:
            raise PermissionError("An active subscription is required.")
        for policy in self._applicable_policies(api.id, route.id):
            if policy.kind == "authorization":
                required = frozenset(policy.configuration.get("scopes", ()))
                if not required <= scope.scopes:
                    raise PermissionError("Required API scopes are missing.")
            if policy.kind == "ip_allowlist":
                address = request.headers.get("x-forwarded-for", "")
                if address not in policy.configuration.get("addresses", ()):
                    raise PermissionError("Client address is not allowed.")

    def _enforce_rate_limit(
        self, api: ManagedApi, route: Route, request: GatewayRequest, scope: ApiScope
    ) -> None:
        targets = (f"route:{route.id}", f"consumer:{request.consumer}", "tenant")
        now = monotonic()
        with self._lock:
            for target in targets:
                limit = self.rate_limits.get(self._key(target, scope))
                if limit is None:
                    continue
                bucket = self._requests[self._key(f"{target}:{api.id}", scope)]
                while bucket and bucket[0] <= now - 60:
                    bucket.popleft()
                per_second = sum(timestamp > now - 1 for timestamp in bucket)
                if (
                    per_second >= limit.requests_per_second + limit.burst
                    or len(bucket) >= limit.requests_per_minute
                ):
                    self.metrics.increment("api_rate_limit_rejections_total")
                    raise RuntimeError("Rate limit exceeded.")
                bucket.append(now)

    def _enforce_quota(
        self, api: ManagedApi, request: GatewayRequest, scope: ApiScope
    ) -> None:
        for target in (f"consumer:{request.consumer}", "tenant"):
            quota = self.quotas.get(self._key(target, scope))
            if quota is None:
                continue
            usage = self._usage[self._key(f"{target}:{api.id}", scope)]
            if (
                usage["requests"] + 1 > quota.request_quota
                or usage["tokens"] + request.tokens > quota.token_quota
                or usage["bytes"] + len(request.body) > quota.data_transfer_bytes
            ):
                self.metrics.increment("api_quota_rejections_total")
                raise RuntimeError("Quota exceeded.")
            usage["requests"] += 1
            usage["tokens"] += request.tokens
            usage["bytes"] += len(request.body)

    def _transform_request(
        self, request: GatewayRequest, api: ManagedApi, route: Route
    ) -> GatewayRequest:
        headers = dict(request.headers)
        for policy in self._applicable_policies(api.id, route.id):
            if policy.kind in {"header", "transformation"}:
                headers.update(policy.configuration.get("request_headers", {}))
                for name in policy.configuration.get("remove_request_headers", ()):
                    headers.pop(str(name), None)
        return GatewayRequest(
            request.path,
            request.method,
            headers,
            request.body,
            request.consumer,
            request.tokens,
        )

    def _transform_response(
        self, response: GatewayResponse, api: ManagedApi, route: Route
    ) -> GatewayResponse:
        headers = dict(response.headers)
        for policy in self._applicable_policies(api.id, route.id):
            if policy.kind in {"cors", "header", "transformation"}:
                headers.update(policy.configuration.get("response_headers", {}))
                for name in policy.configuration.get("remove_response_headers", ()):
                    headers.pop(str(name), None)
        return GatewayResponse(response.status_code, headers, response.body)

    def _cache_key(self, api: ManagedApi, request: GatewayRequest) -> str:
        digest = hashlib.sha256(
            b"\0".join((request.path.encode(), request.body, request.consumer.encode()))
        ).hexdigest()
        return f"{api.id}:{digest}"

    def _cache_response(
        self, api: ManagedApi, key: str, response: GatewayResponse
    ) -> None:
        policy = self.caches.get(api.id)
        sensitive = any(
            name.lower() in {"authorization", "set-cookie"}
            for name in response.headers
        )
        if (
            policy is None
            or response.status_code >= 400
            or (policy.exclude_sensitive and sensitive)
        ):
            return
        if len(self._cache) >= policy.max_entries:
            self._cache.pop(next(iter(self._cache)))
        self._cache[key] = (monotonic() + policy.ttl_seconds, response)

    def _record(
        self,
        api: ManagedApi,
        route: Route,
        request: GatewayRequest,
        status_code: int,
        started: float,
    ) -> None:
        self.analytics.append(
            {
                "request_id": secrets.token_hex(12),
                "tenant": api.tenant,
                "workspace": api.workspace,
                "api_id": api.id,
                "route_id": route.id,
                "consumer": request.consumer,
                "latency_seconds": monotonic() - started,
                "status_code": status_code,
                "error": status_code >= 400,
                "occurred_at": utcnow().isoformat(),
            }
        )

    def _applicable_policies(self, api_id: str, route_id: str) -> list[Policy]:
        return [
            policy
            for policy in self.policies.values()
            if policy.enabled
            and (policy.api_id in {None, api_id})
            and (policy.route_id in {None, route_id})
        ]

    def _key(self, target: str, scope: ApiScope) -> str:
        return f"{scope.tenant}:{scope.workspace}:{target}"

    def _configuration(self, values: Mapping[str, Any], scope: ApiScope) -> list[Any]:
        prefix = f"{scope.tenant}:{scope.workspace}:"
        return [
            {"target": key.removeprefix(prefix), **asdict(value)}
            for key, value in values.items()
            if key.startswith(prefix)
        ]

    def _update_consumers(self) -> None:
        active = {
            (item.tenant, item.workspace, item.consumer)
            for item in self.subscriptions.values()
            if item.status is SubscriptionStatus.ACTIVE
            and (item.expiration is None or item.expiration > utcnow())
        }
        self.metrics.set("api_active_consumers_total", float(len(active)))


EnterpriseAIAPIManagementPlatform = ApiManagementPlatform

__all__ = (
    "ApiManagementPlatform",
    "ApiScope",
    "ApiStatus",
    "ApiVersion",
    "AuditEntry",
    "CachePolicy",
    "Credential",
    "EnterpriseAIAPIManagementPlatform",
    "Gateway",
    "GatewayRequest",
    "GatewayResponse",
    "ManagedApi",
    "Policy",
    "Quota",
    "RateLimit",
    "Route",
    "Subscription",
    "SubscriptionStatus",
    "UpstreamHandler",
    "Visibility",
    "utcnow",
)
