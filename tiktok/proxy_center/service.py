"""Enterprise TikTok Proxy Center domain service."""

from __future__ import annotations

import builtins
import heapq
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .metrics import ProxyCenterMetrics
from .models import (
    Allocation,
    AllocationRequest,
    BindingTarget,
    HealthRecord,
    Proxy,
    ProxyBinding,
    ProxyGroup,
    ProxyScope,
    ProxyStatus,
    RotationPolicy,
    UsageEvent,
    VerificationResult,
)
from .security import ReferenceSecretResolver, SecretResolver, sanitized_metadata
from .verification import ProxyVerifier


class TikTokProxyCenter:
    """Tenant-scoped in-process control plane with bounded resource limits."""

    def __init__(
        self,
        *,
        secret_resolver: SecretResolver | None = None,
        verifier: ProxyVerifier | None = None,
        minimum_pool_size: int = 0,
        maximum_pool_size: int = 1000,
        maximum_concurrency: int = 100,
        maximum_queue_size: int = 4000,
    ) -> None:
        if not 0 <= minimum_pool_size <= maximum_pool_size:
            raise ValueError("Pool size bounds are invalid.")
        if minimum_pool_size > maximum_concurrency or maximum_concurrency < 1:
            raise ValueError("Concurrency must cover the minimum pool size.")
        if maximum_queue_size < 1:
            raise ValueError("Queue size must be positive.")
        self.proxies: dict[str, Proxy] = {}
        self.groups: dict[str, ProxyGroup] = {}
        self.bindings: dict[str, ProxyBinding] = {}
        self.rotation_policies: dict[str, RotationPolicy] = {}
        self.health: dict[str, HealthRecord] = {}
        self.verifications: dict[str, VerificationResult] = {}
        self.allocations: dict[str, Allocation] = {}
        self.usage: list[UsageEvent] = []
        self.rotation_history: list[dict[str, str]] = []
        self.audit: list[dict[str, str]] = []
        self._queue: list[AllocationRequest] = []
        self._fairness: Counter[tuple[str, str]] = Counter()
        self.minimum_pool_size = minimum_pool_size
        self.maximum_pool_size = maximum_pool_size
        self.maximum_concurrency = maximum_concurrency
        self.maximum_queue_size = maximum_queue_size
        self.secrets = secret_resolver or ReferenceSecretResolver()
        self.verifier = verifier or ProxyVerifier()
        self.metrics = ProxyCenterMetrics()

    @staticmethod
    def _require(scope: ProxyScope, action: str) -> None:
        required = f"tiktok:proxy:{action}"
        if (
            required not in scope.permissions
            and "tiktok:proxy:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    @staticmethod
    def _scoped(item: Any, scope: ProxyScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-workspace Proxy Center access denied.")

    def _audit(self, action: str, resource: str, scope: ProxyScope) -> None:
        self.audit.append(
            {
                "action": action,
                "resource": resource,
                "actor": scope.actor,
                "tenant": scope.tenant,
                "workspace": scope.workspace,
            }
        )

    def _refresh_metrics(self) -> None:
        active = sum(
            item.status in {ProxyStatus.AVAILABLE, ProxyStatus.IN_USE}
            for item in self.proxies.values()
        )
        depth = sum(
            item.status is ProxyStatus.AVAILABLE for item in self.proxies.values()
        )
        scores = [record.health_score for record in self.health.values()]
        self.metrics.set("tiktok_proxy_active_total", active)
        self.metrics.set("tiktok_proxy_pool_depth", depth)
        self.metrics.set(
            "tiktok_proxy_health_score", sum(scores) / len(scores) if scores else 0
        )

    def create(self, proxy: Proxy, scope: ProxyScope) -> Proxy:
        self._require(scope, "write")
        self._scoped(proxy, scope)
        proxy.validate()
        if proxy.id in self.proxies:
            raise ValueError("Proxy ID must be unique.")
        scoped_count = sum(
            item.tenant == scope.tenant
            and item.workspace == scope.workspace
            and item.status is not ProxyStatus.DELETED
            for item in self.proxies.values()
        )
        if scoped_count >= self.maximum_pool_size:
            raise RuntimeError("Maximum proxy pool size reached.")
        if not self.secrets.exists(
            proxy.credential_reference, scope.tenant, scope.workspace
        ):
            raise ValueError(
                "Credential reference does not exist in encrypted storage."
            )
        proxy.metadata = sanitized_metadata(proxy.metadata)
        self.proxies[proxy.id] = proxy
        self.metrics.increment("tiktok_proxies_total")
        self._refresh_metrics()
        self._audit("proxy.create", proxy.id, scope)
        return proxy

    def get(self, proxy_id: str, scope: ProxyScope) -> Proxy:
        self._require(scope, "read")
        proxy = self.proxies[proxy_id]
        self._scoped(proxy, scope)
        return proxy

    def list(self, scope: ProxyScope, *, include_deleted: bool = False) -> list[Proxy]:
        self._require(scope, "read")
        return [
            item
            for item in self.proxies.values()
            if item.tenant == scope.tenant
            and item.workspace == scope.workspace
            and (include_deleted or item.status is not ProxyStatus.DELETED)
        ]

    def update(self, proxy_id: str, scope: ProxyScope, **changes: Any) -> Proxy:
        self._require(scope, "write")
        proxy = self.get(
            proxy_id,
            ProxyScope(
                scope.tenant,
                scope.workspace,
                scope.actor,
                scope.permissions | {"tiktok:proxy:read"},
            ),
        )
        immutable = {"id", "tenant", "workspace"}
        if immutable & changes.keys():
            raise ValueError("Proxy identity and isolation scope are immutable.")
        for key, value in changes.items():
            if not hasattr(proxy, key):
                raise ValueError(f"Unknown proxy field: {key}")
            setattr(proxy, key, value)
        proxy.updated_at = datetime.now(timezone.utc)
        proxy.validate()
        self._audit("proxy.update", proxy.id, scope)
        return proxy

    def transition(
        self, proxy_id: str, status: ProxyStatus, scope: ProxyScope
    ) -> Proxy:
        self._require(scope, "write")
        proxy = self.get(
            proxy_id,
            ProxyScope(
                scope.tenant,
                scope.workspace,
                scope.actor,
                scope.permissions | {"tiktok:proxy:read"},
            ),
        )
        transitions = {
            ProxyStatus.DRAFT: {
                ProxyStatus.AVAILABLE,
                ProxyStatus.DISABLED,
                ProxyStatus.DELETED,
            },
            ProxyStatus.AVAILABLE: {
                ProxyStatus.IN_USE,
                ProxyStatus.DISABLED,
                ProxyStatus.EXPIRED,
                ProxyStatus.ARCHIVED,
            },
            ProxyStatus.IN_USE: {
                ProxyStatus.AVAILABLE,
                ProxyStatus.COOLING,
                ProxyStatus.DISABLED,
            },
            ProxyStatus.COOLING: {
                ProxyStatus.AVAILABLE,
                ProxyStatus.DISABLED,
                ProxyStatus.EXPIRED,
            },
            ProxyStatus.DISABLED: {
                ProxyStatus.AVAILABLE,
                ProxyStatus.ARCHIVED,
                ProxyStatus.DELETED,
            },
            ProxyStatus.EXPIRED: {ProxyStatus.ARCHIVED, ProxyStatus.DELETED},
            ProxyStatus.ARCHIVED: {ProxyStatus.DELETED},
            ProxyStatus.DELETED: set(),
        }
        if status not in transitions[proxy.status]:
            raise ValueError(
                f"Invalid proxy transition: {proxy.status.value} -> {status.value}"
            )
        proxy.status = status
        proxy.updated_at = datetime.now(timezone.utc)
        self._refresh_metrics()
        self._audit(f"proxy.{status.value}", proxy.id, scope)
        return proxy

    def delete(self, proxy_id: str, scope: ProxyScope) -> Proxy:
        proxy = self.get(
            proxy_id,
            ProxyScope(
                scope.tenant,
                scope.workspace,
                scope.actor,
                scope.permissions | {"tiktok:proxy:read"},
            ),
        )
        if proxy.status not in {
            ProxyStatus.DRAFT,
            ProxyStatus.DISABLED,
            ProxyStatus.EXPIRED,
            ProxyStatus.ARCHIVED,
        }:
            raise ValueError("Proxy must be inactive before deletion.")
        return self.transition(proxy_id, ProxyStatus.DELETED, scope)

    def create_group(self, group: ProxyGroup, scope: ProxyScope) -> ProxyGroup:
        self._require(scope, "write")
        self._scoped(group, scope)
        if not group.id or group.id in self.groups:
            raise ValueError("Group ID must be non-empty and unique.")
        for proxy_id in group.proxy_ids:
            self.get(
                proxy_id,
                ProxyScope(
                    scope.tenant,
                    scope.workspace,
                    scope.actor,
                    scope.permissions | {"tiktok:proxy:read"},
                ),
            )
        self.groups[group.id] = group
        self._audit("group.create", group.id, scope)
        return group

    def create_binding(self, binding: ProxyBinding, scope: ProxyScope) -> ProxyBinding:
        self._require(scope, "bind")
        self._scoped(binding, scope)
        if not binding.id or binding.id in self.bindings:
            raise ValueError("Binding ID must be non-empty and unique.")
        if bool(binding.proxy_reference) == bool(binding.group_reference):
            raise ValueError("Binding requires exactly one proxy or group reference.")
        if binding.proxy_reference:
            self.get(
                binding.proxy_reference,
                ProxyScope(
                    scope.tenant,
                    scope.workspace,
                    scope.actor,
                    scope.permissions | {"tiktok:proxy:read"},
                ),
            )
        elif binding.group_reference not in self.groups:
            raise KeyError(binding.group_reference)
        self.bindings[binding.id] = binding
        self._audit("binding.create", binding.id, scope)
        return binding

    def create_rotation_policy(
        self, policy: RotationPolicy, scope: ProxyScope
    ) -> RotationPolicy:
        self._require(scope, "rotate")
        self._scoped(policy, scope)
        if policy.id in self.rotation_policies or policy.cooldown_seconds < 0:
            raise ValueError("Rotation policy is invalid or duplicated.")
        self.rotation_policies[policy.id] = policy
        self._audit("rotation.policy.create", policy.id, scope)
        return policy

    def verify(self, proxy_id: str, scope: ProxyScope) -> VerificationResult:
        self._require(scope, "verify")
        proxy = self.get(
            proxy_id,
            ProxyScope(
                scope.tenant,
                scope.workspace,
                scope.actor,
                scope.permissions | {"tiktok:proxy:read"},
            ),
        )
        result = self.verifier.verify(proxy)
        self.verifications[proxy.id] = result
        successful = 1.0 if result.successful else 0.0
        previous = self.health.get(proxy.id)
        failures = (
            0
            if result.successful
            else (previous.consecutive_failures + 1 if previous else 1)
        )
        score = max(
            0.0, min(100.0, successful * 70 + (30 if result.public_ip_check else 0))
        )
        self.health[proxy.id] = HealthRecord(
            proxy.id,
            result.tcp_connectivity,
            result.latency_seconds,
            availability=successful * 100,
            success_rate=successful * 100,
            failure_rate=(1 - successful) * 100,
            consecutive_failures=failures,
            health_score=score,
            checks={
                "dns_resolution": result.dns_resolution,
                "tcp_connectivity": result.tcp_connectivity,
                "tls_handshake": result.tls_handshake,
                "public_ip_check": result.public_ip_check,
                "geo_check": result.geo_check,
                "protocol_validation": result.protocol_validation,
                "authentication_validation": result.authentication_validation,
            },
        )
        self.metrics.set("tiktok_proxy_latency_seconds", result.latency_seconds)
        if not result.successful:
            self.metrics.increment("tiktok_proxy_failures_total")
        self._refresh_metrics()
        self._audit("proxy.verify", proxy.id, scope)
        return result

    def _candidates(
        self,
        scope: ProxyScope,
        target_type: BindingTarget,
        target_reference: str,
        region: str,
        country: str,
    ) -> builtins.list[Proxy]:
        bound_ids: set[str] = set()
        matching = sorted(
            (
                item
                for item in self.bindings.values()
                if item.tenant == scope.tenant
                and item.workspace == scope.workspace
                and item.target_type is target_type
                and item.target_reference == target_reference
            ),
            key=lambda item: item.priority,
            reverse=True,
        )
        for binding in matching:
            if binding.proxy_reference:
                bound_ids.add(binding.proxy_reference)
            elif binding.group_reference in self.groups:
                bound_ids |= self.groups[binding.group_reference].proxy_ids
        candidates = [
            proxy
            for proxy in self.list(scope)
            if proxy.status is ProxyStatus.AVAILABLE
            and (not bound_ids or proxy.id in bound_ids)
            and (not region or proxy.region.casefold() == region.casefold())
            and (not country or proxy.country.casefold() == country.casefold())
        ]
        return sorted(
            candidates,
            key=lambda item: (
                -(self.health[item.id].health_score if item.id in self.health else 50),
                self._fairness[(scope.workspace, item.id)],
                item.id,
            ),
        )

    def acquire(
        self,
        scope: ProxyScope,
        *,
        target_type: BindingTarget,
        target_reference: str,
        region: str = "",
        country: str = "",
        reserve: bool = False,
    ) -> Allocation:
        self._require(scope, "acquire")
        active = sum(
            item.released_at is None
            and item.tenant == scope.tenant
            and item.workspace == scope.workspace
            for item in self.allocations.values()
        )
        if active >= self.maximum_concurrency:
            raise RuntimeError("Proxy allocation concurrency limit reached.")
        candidates = self._candidates(
            scope, target_type, target_reference, region, country
        )
        if not candidates:
            raise RuntimeError("No healthy matching proxy is available.")
        proxy = candidates[0]
        proxy.status = ProxyStatus.IN_USE
        allocation = Allocation(
            str(uuid4()),
            proxy.id,
            scope.tenant,
            scope.workspace,
            target_type,
            target_reference,
            reserved=reserve,
        )
        self.allocations[allocation.id] = allocation
        self._fairness[(scope.workspace, proxy.id)] += 1
        self._refresh_metrics()
        self._audit("pool.reserve" if reserve else "pool.acquire", allocation.id, scope)
        return allocation

    def release(self, allocation_id: str, scope: ProxyScope) -> Allocation:
        self._require(scope, "release")
        allocation = self.allocations[allocation_id]
        self._scoped(allocation, scope)
        if allocation.released_at is not None:
            raise ValueError("Allocation has already been released.")
        allocation.released_at = datetime.now(timezone.utc)
        allocation.reserved = False
        proxy = self.proxies[allocation.proxy_id]
        if not any(
            item.proxy_id == proxy.id and item.released_at is None
            for item in self.allocations.values()
        ):
            proxy.status = ProxyStatus.AVAILABLE
        self._refresh_metrics()
        self._audit("pool.release", allocation.id, scope)
        return allocation

    def recycle(self, proxy_id: str, scope: ProxyScope) -> Proxy:
        self._require(scope, "admin")
        proxy = self.get(
            proxy_id,
            ProxyScope(
                scope.tenant,
                scope.workspace,
                scope.actor,
                scope.permissions | {"tiktok:proxy:read"},
            ),
        )
        if proxy.status not in {ProxyStatus.COOLING, ProxyStatus.DISABLED}:
            raise ValueError("Only cooling or disabled proxies can be recycled.")
        proxy.status = ProxyStatus.AVAILABLE
        self._audit("pool.recycle", proxy.id, scope)
        self._refresh_metrics()
        return proxy

    def drain(self, scope: ProxyScope) -> int:
        self._require(scope, "admin")
        count = 0
        for proxy in self.list(scope):
            if proxy.status in {ProxyStatus.AVAILABLE, ProxyStatus.COOLING}:
                proxy.status = ProxyStatus.DISABLED
                count += 1
        self._refresh_metrics()
        self._audit("pool.drain", str(count), scope)
        return count

    def enqueue(
        self,
        scope: ProxyScope,
        target_type: BindingTarget,
        target_reference: str,
        *,
        priority: int = 0,
        region: str = "",
        country: str = "",
        retries: int = 2,
        timeout_seconds: float = 10,
    ) -> AllocationRequest:
        self._require(scope, "acquire")
        if len(self._queue) >= self.maximum_queue_size:
            raise RuntimeError("Proxy scheduler queue limit reached.")
        if not 0 < timeout_seconds <= 60 or not 0 <= retries <= 10:
            raise ValueError("Scheduler retry or timeout bound exceeded.")
        fairness = self._fairness[(scope.tenant, scope.workspace)]
        request = AllocationRequest(
            (-priority, datetime.now(timezone.utc), fairness),
            str(uuid4()),
            scope.tenant,
            scope.workspace,
            target_type,
            target_reference,
            priority,
            region,
            country,
            timeout_seconds,
            retries,
        )
        heapq.heappush(self._queue, request)
        return request

    def schedule_next(self, scope: ProxyScope) -> Allocation | None:
        self._require(scope, "acquire")
        deferred: list[AllocationRequest] = []
        result: Allocation | None = None
        while self._queue:
            request = heapq.heappop(self._queue)
            if request.cancelled:
                continue
            if request.tenant != scope.tenant or request.workspace != scope.workspace:
                deferred.append(request)
                continue
            try:
                result = self.acquire(
                    scope,
                    target_type=request.target_type,
                    target_reference=request.target_reference,
                    region=request.region_preference,
                    country=request.country_preference,
                )
            except RuntimeError:
                if request.retries:
                    request.retries -= 1
                    request.sort_key = (
                        request.sort_key[0],
                        datetime.now(timezone.utc),
                        request.sort_key[2] + 1,
                    )
                    deferred.append(request)
            break
        for item in deferred:
            heapq.heappush(self._queue, item)
        return result

    def rotate(
        self, allocation_id: str, scope: ProxyScope, *, reason: str = "manual"
    ) -> Allocation:
        self._require(scope, "rotate")
        current = self.allocations[allocation_id]
        self._scoped(current, scope)
        old_proxy = current.proxy_id
        self.release(
            allocation_id,
            ProxyScope(
                scope.tenant,
                scope.workspace,
                scope.actor,
                scope.permissions | {"tiktok:proxy:release"},
            ),
        )
        new = self.acquire(
            ProxyScope(
                scope.tenant,
                scope.workspace,
                scope.actor,
                scope.permissions | {"tiktok:proxy:acquire"},
            ),
            target_type=current.target_type,
            target_reference=current.target_reference,
        )
        self.rotation_history.append(
            {"from": old_proxy, "to": new.proxy_id, "reason": reason}
        )
        self.metrics.increment("tiktok_proxy_rotations_total")
        self._audit("proxy.rotate", new.id, scope)
        return new

    def record_usage(
        self,
        proxy_id: str,
        scope: ProxyScope,
        *,
        successful: bool,
        latency_seconds: float,
        allocation_id: str = "",
    ) -> UsageEvent:
        self._require(scope, "write")
        self.get(
            proxy_id,
            ProxyScope(
                scope.tenant,
                scope.workspace,
                scope.actor,
                scope.permissions | {"tiktok:proxy:read"},
            ),
        )
        if latency_seconds < 0:
            raise ValueError("Latency cannot be negative.")
        event = UsageEvent(
            proxy_id,
            scope.tenant,
            scope.workspace,
            successful,
            latency_seconds,
            allocation_id,
        )
        self.usage.append(event)
        self.metrics.set("tiktok_proxy_latency_seconds", latency_seconds)
        if not successful:
            self.metrics.increment("tiktok_proxy_failures_total")
        return event

    def statistics(self, scope: ProxyScope) -> dict[str, Any]:
        self._require(scope, "read")
        events = [
            event
            for event in self.usage
            if event.tenant == scope.tenant and event.workspace == scope.workspace
        ]
        allocations = [
            item
            for item in self.allocations.values()
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]
        return {
            "usage": len(events),
            "success": sum(item.successful for item in events),
            "failure": sum(not item.successful for item in events),
            "average_latency": (
                sum(item.latency_seconds for item in events) / len(events)
                if events
                else 0
            ),
            "peak_usage": max(
                Counter(item.proxy_id for item in allocations).values(), default=0
            ),
            "allocation_history": [asdict(item) for item in allocations],
            "rotation_history": list(self.rotation_history),
        }

    def dashboard(self, scope: ProxyScope) -> dict[str, Any]:
        proxies = self.list(scope)
        identifiers = {item.id for item in proxies}
        return {
            "sections": [
                "Proxy Inventory",
                "Health",
                "Regions",
                "Countries",
                "Groups",
                "Bindings",
                "Pool",
                "Queue",
                "Statistics",
                "Failures",
            ],
            "proxy_inventory": len(proxies),
            "health": {
                key: value.health_score
                for key, value in self.health.items()
                if key in identifiers
            },
            "regions": sorted({item.region for item in proxies if item.region}),
            "countries": sorted({item.country for item in proxies if item.country}),
            "groups": sum(
                item.tenant == scope.tenant and item.workspace == scope.workspace
                for item in self.groups.values()
            ),
            "bindings": sum(
                item.tenant == scope.tenant and item.workspace == scope.workspace
                for item in self.bindings.values()
            ),
            "pool": {
                "minimum": self.minimum_pool_size,
                "maximum": self.maximum_pool_size,
                "depth": sum(item.status is ProxyStatus.AVAILABLE for item in proxies),
                "concurrency_limit": self.maximum_concurrency,
            },
            "queue": sum(
                item.tenant == scope.tenant
                and item.workspace == scope.workspace
                and not item.cancelled
                for item in self._queue
            ),
            "statistics": self.statistics(scope),
            "failures": sum(
                record.consecutive_failures
                for record in self.health.values()
                if record.proxy_id in identifiers
            ),
        }
