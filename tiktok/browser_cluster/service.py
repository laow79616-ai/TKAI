"""Resource-bounded scheduler for local TikTok browser runtimes."""
from __future__ import annotations

import heapq
from datetime import datetime, timezone
from time import monotonic
from typing import Any
from uuid import uuid4

from .adapters import (
    BrowserRuntimePort,
    PermissiveRiskControl,
    ReferenceBrowserRuntime,
    RiskControlPort,
)
from .metrics import BrowserClusterMetrics
from .models import (
    BrowserCluster,
    BrowserProfileTemplate,
    ClusterBrowserInstance,
    ClusterNode,
    ClusterScope,
    ClusterStatus,
    InstanceStatus,
    NodeStatus,
    QueueItem,
    RecoveryPolicy,
    RecoveryRecord,
    ResourcePolicy,
    serialize,
)


class TikTokBrowserCluster:
    """Single-user local cluster with isolation, fairness, and bounded recovery."""

    def __init__(
        self,
        *,
        runtime: BrowserRuntimePort | None = None,
        risk_control: RiskControlPort | None = None,
        resources: ResourcePolicy | None = None,
        recovery: RecoveryPolicy | None = None,
    ) -> None:
        self.runtime = runtime or ReferenceBrowserRuntime()
        self.risk_control = risk_control or PermissiveRiskControl()
        self.resources = resources or ResourcePolicy()
        self.recovery_policy = recovery or RecoveryPolicy()
        self.resources.validate()
        self.recovery_policy.validate()
        self.clusters: dict[str, BrowserCluster] = {}
        self.nodes: dict[str, ClusterNode] = {}
        self.instances: dict[str, ClusterBrowserInstance] = {}
        self.profiles: dict[str, BrowserProfileTemplate] = {}
        self.recoveries: list[RecoveryRecord] = []
        self.audit: list[dict[str, str]] = []
        self._queue: list[QueueItem] = []
        self._sequence = 0
        self.metrics = BrowserClusterMetrics()

    @staticmethod
    def _require(scope: ClusterScope, action: str) -> None:
        required = f"tiktok:browser-cluster:{action}"
        if required not in scope.permissions and (
            "tiktok:browser-cluster:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    @staticmethod
    def _scoped(value: Any, scope: ClusterScope) -> None:
        if value.tenant != scope.tenant or value.workspace != scope.workspace:
            raise PermissionError("Cross-workspace browser cluster access denied.")

    def _audit(self, action: str, resource: str, scope: ClusterScope) -> None:
        self.audit.append(
            {
                "action": action,
                "resource": resource,
                "tenant": scope.tenant,
                "workspace": scope.workspace,
                "actor": scope.actor,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def create_cluster(
        self, cluster: BrowserCluster, scope: ClusterScope
    ) -> BrowserCluster:
        self._require(scope, "write")
        self._scoped(cluster, scope)
        if not cluster.id or cluster.id in self.clusters:
            raise ValueError("Cluster ID must be non-empty and unique.")
        cluster.metadata = {
            key: value
            for key, value in cluster.metadata.items()
            if "secret" not in key.lower() and "token" not in key.lower()
        }
        self.clusters[cluster.id] = cluster
        self.metrics.set("tiktok_browser_cluster_total", len(self.clusters))
        self._audit("cluster.create", cluster.id, scope)
        return cluster

    def create_profile(
        self, profile: BrowserProfileTemplate, scope: ClusterScope
    ) -> BrowserProfileTemplate:
        self._require(scope, "write")
        self._scoped(profile, scope)
        profile.validate()
        current = self.profiles.get(profile.id)
        if current is not None and profile.version <= current.version:
            raise ValueError("Profile version must increase.")
        self.profiles[profile.id] = profile
        self._audit("profile.version", profile.id, scope)
        return profile

    def transition(
        self, cluster_id: str, status: ClusterStatus, scope: ClusterScope
    ) -> BrowserCluster:
        self._require(scope, "control")
        cluster = self.clusters[cluster_id]
        self._scoped(cluster, scope)
        allowed = {
            ClusterStatus.INITIALIZING: {ClusterStatus.READY, ClusterStatus.DELETED},
            ClusterStatus.READY: {
                ClusterStatus.RUNNING,
                ClusterStatus.MAINTENANCE,
                ClusterStatus.ARCHIVED,
            },
            ClusterStatus.RUNNING: {
                ClusterStatus.SCALING,
                ClusterStatus.PAUSED,
                ClusterStatus.RECOVERING,
                ClusterStatus.MAINTENANCE,
            },
            ClusterStatus.SCALING: {ClusterStatus.RUNNING, ClusterStatus.RECOVERING},
            ClusterStatus.PAUSED: {ClusterStatus.RUNNING, ClusterStatus.MAINTENANCE},
            ClusterStatus.RECOVERING: {
                ClusterStatus.RUNNING,
                ClusterStatus.PAUSED,
                ClusterStatus.MAINTENANCE,
            },
            ClusterStatus.MAINTENANCE: {
                ClusterStatus.READY,
                ClusterStatus.ARCHIVED,
            },
            ClusterStatus.ARCHIVED: {ClusterStatus.DELETED},
            ClusterStatus.DELETED: set(),
        }
        if status not in allowed[cluster.status]:
            message = f"Invalid cluster transition: {cluster.status} -> {status}"
            raise ValueError(message)
        cluster.status = status
        self._audit("cluster.transition", cluster.id, scope)
        return cluster

    def register_node(self, node: ClusterNode, scope: ClusterScope) -> ClusterNode:
        self._require(scope, "write")
        self._scoped(node, scope)
        cluster = self.clusters[node.cluster_id]
        self._scoped(cluster, scope)
        if not node.id or node.id in self.nodes:
            raise ValueError("Node ID must be non-empty and unique.")
        if min(
            node.capacity,
            node.cpu_capacity,
            node.memory_capacity_mb,
            node.browser_slots,
        ) <= 0:
            raise ValueError("Node capacity values must be positive.")
        self.nodes[node.id] = node
        self._refresh_metrics()
        self._audit("node.register", node.id, scope)
        return node

    def heartbeat(
        self,
        node_id: str,
        scope: ClusterScope,
        *,
        cpu_usage: float,
        memory_usage_mb: int,
    ) -> ClusterNode:
        self._require(scope, "control")
        node = self.nodes[node_id]
        self._scoped(node, scope)
        if not 0 <= cpu_usage <= node.cpu_capacity:
            raise ValueError("CPU usage exceeds node capacity.")
        if not 0 <= memory_usage_mb <= node.memory_capacity_mb:
            raise ValueError("Memory usage exceeds node capacity.")
        node.cpu_usage = cpu_usage
        node.memory_usage_mb = memory_usage_mb
        node.heartbeat = datetime.now(timezone.utc)
        node.health = "healthy"
        self._refresh_metrics()
        return node

    def create_instance(
        self, instance: ClusterBrowserInstance, scope: ClusterScope
    ) -> ClusterBrowserInstance:
        self._require(scope, "write")
        self._scoped(instance, scope)
        if not instance.id or instance.id in self.instances:
            raise ValueError("Instance ID must be non-empty and unique.")
        if not instance.browser_runtime_reference:
            raise ValueError("Browser Runtime reference is required.")
        self.instances[instance.id] = instance
        self._refresh_metrics()
        self._audit("instance.create", instance.id, scope)
        return instance

    def enqueue(
        self, instance_id: str, scope: ClusterScope, *, priority: int = 0
    ) -> QueueItem:
        self._require(scope, "schedule")
        instance = self.instances[instance_id]
        self._scoped(instance, scope)
        if any(item.instance_id == instance_id for item in self._queue):
            raise ValueError("Instance is already queued.")
        self._sequence += 1
        now = datetime.now(timezone.utc)
        item = QueueItem(
            (-priority, now, self._sequence),
            str(uuid4()),
            instance.id,
            scope.tenant,
            scope.workspace,
            instance.account_reference,
            priority,
        )
        heapq.heappush(self._queue, item)
        instance.status = InstanceStatus.QUEUED
        self._refresh_metrics()
        self._audit("queue.enqueue", item.id, scope)
        return item

    def _eligible_node(self, instance: ClusterBrowserInstance) -> ClusterNode | None:
        candidates = [
            node
            for node in self.nodes.values()
            if node.tenant == instance.tenant
            and node.workspace == instance.workspace
            and node.status is NodeStatus.READY
            and node.running_browsers + node.idle_browsers < node.browser_slots
            and node.cpu_usage + instance.cpu_reservation <= node.cpu_capacity
            and node.memory_usage_mb + instance.memory_reservation_mb
            <= node.memory_capacity_mb
        ]
        return min(
            candidates,
            key=lambda node: (
                node.running_browsers + node.idle_browsers,
                node.cpu_usage,
                node.id,
            ),
            default=None,
        )

    def process_queue(
        self, scope: ClusterScope, *, limit: int | None = None
    ) -> list[str]:
        self._require(scope, "schedule")
        cap = min(
            limit or self.resources.maximum_parallel_launches,
            self.resources.maximum_parallel_launches,
        )
        launched: list[str] = []
        deferred: list[QueueItem] = []
        while self._queue and len(launched) < cap:
            item = heapq.heappop(self._queue)
            if item.tenant != scope.tenant or item.workspace != scope.workspace:
                deferred.append(item)
                continue
            instance = self.instances[item.instance_id]
            active = [
                value
                for value in self.instances.values()
                if value.status in {InstanceStatus.RUNNING, InstanceStatus.IDLE}
            ]
            if (
                len(active) >= self.resources.maximum_browser_count
                or sum(
                    value.tenant == scope.tenant
                    and value.workspace == scope.workspace
                    for value in active
                )
                >= self.resources.workspace_limit
                or sum(
                    value.account_reference == instance.account_reference
                    and value.tenant == scope.tenant
                    and value.workspace == scope.workspace
                    for value in active
                )
                >= self.resources.account_limit
            ):
                deferred.append(item)
                continue
            node = self._eligible_node(instance)
            if node is None:
                deferred.append(item)
                continue
            started = monotonic()
            instance.status = InstanceStatus.LAUNCHING
            try:
                self.runtime.launch_reference(instance)
                instance.status = InstanceStatus.RUNNING
                instance.health = "healthy"
                instance.node_id = node.id
                instance.last_active = datetime.now(timezone.utc)
                node.running_browsers += 1
                node.cpu_usage += instance.cpu_reservation
                node.memory_usage_mb += instance.memory_reservation_mb
                launched.append(instance.id)
            except Exception:
                instance.status = InstanceStatus.FAILED
                instance.health = "failed"
                self.metrics.increment("tiktok_browser_cluster_failures")
            self.metrics.set(
                "tiktok_browser_cluster_launch_latency_seconds",
                monotonic() - started,
            )
        for item in deferred:
            heapq.heappush(self._queue, item)
        self._refresh_metrics()
        return launched

    def release(self, instance_id: str, scope: ClusterScope) -> None:
        self._require(scope, "control")
        instance = self.instances[instance_id]
        self._scoped(instance, scope)
        self.runtime.stop_reference(instance.browser_runtime_reference)
        node = self.nodes.get(instance.node_id)
        if node is not None:
            node.running_browsers = max(0, node.running_browsers - 1)
            node.idle_browsers = max(0, node.idle_browsers - 1)
            node.cpu_usage = max(0.0, node.cpu_usage - instance.cpu_reservation)
            node.memory_usage_mb = max(
                0, node.memory_usage_mb - instance.memory_reservation_mb
            )
        instance.status = InstanceStatus.STOPPED
        instance.node_id = ""
        self._refresh_metrics()
        self._audit("resource.release", instance.id, scope)

    def recover(
        self,
        instance_id: str,
        scope: ClusterScope,
        *,
        reason: str,
        approved: bool = False,
    ) -> RecoveryRecord:
        self._require(scope, "recover")
        instance = self.instances[instance_id]
        self._scoped(instance, scope)
        restricted = self.risk_control.has_unresolved_restriction(
            scope.tenant, scope.workspace, instance.account_reference
        )
        previous = sum(item.instance_id == instance.id for item in self.recoveries)
        if restricted or (
            self.recovery_policy.manual_approval and not approved
        ) or previous >= self.recovery_policy.maximum_attempts:
            instance.status = InstanceStatus.PAUSED
            record = RecoveryRecord(
                instance.id,
                previous,
                reason,
                "manual_review",
                False,
                stopped_for_restriction=restricted,
            )
        else:
            instance.status = InstanceStatus.RECOVERING
            restored = self.runtime.restore_reference(
                instance.browser_runtime_reference
            )
            instance.status = (
                InstanceStatus.RUNNING if restored else InstanceStatus.FAILED
            )
            instance.health = "healthy" if restored else "failed"
            record = RecoveryRecord(
                instance.id, previous + 1, reason, "session_restore", restored
            )
        self.recoveries.append(record)
        self.metrics.increment("tiktok_browser_cluster_recoveries")
        self._audit("recovery.attempt", instance.id, scope)
        return record

    def health(self, scope: ClusterScope) -> dict[str, Any]:
        self._require(scope, "read")
        nodes = self._scope_values(self.nodes, scope)
        instances = self._scope_values(self.instances, scope)
        failures = sum(item.status is InstanceStatus.FAILED for item in instances)
        score = max(
            0.0,
            100.0
            - failures * 15.0
            - sum(node.health != "healthy" for node in nodes) * 20.0,
        )
        return {
            "score": score,
            "node_health": {node.id: node.health for node in nodes},
            "browser_health": {item.id: item.health for item in instances},
            "queue_health": "healthy" if len(self._queue) < 100 else "degraded",
            "resource_health": "healthy"
            if any(node.running_browsers < node.browser_slots for node in nodes)
            else "saturated",
            "recovery_health": "manual_review"
            if any(item.stopped_for_restriction for item in self.recoveries)
            else "healthy",
        }

    def statistics(self, scope: ClusterScope) -> dict[str, float | int]:
        self._require(scope, "read")
        values = self._scope_values(self.instances, scope)
        running = sum(item.status is InstanceStatus.RUNNING for item in values)
        idle = sum(item.status is InstanceStatus.IDLE for item in values)
        ids = {value.id for value in values}
        recoveries = [item for item in self.recoveries if item.instance_id in ids]
        return {
            "running_browsers": running,
            "idle_browsers": idle,
            "peak_browsers": max(
                running + idle,
                int(self.metrics.values["tiktok_browser_cluster_running"]),
            ),
            "average_runtime_seconds": 0.0,
            "average_launch_time_seconds": self.metrics.values[
                "tiktok_browser_cluster_launch_latency_seconds"
            ],
            "recovery_success": (
                sum(item.recovered for item in recoveries) / len(recoveries)
                if recoveries
                else 0.0
            ),
            "cpu_usage": sum(node.cpu_usage for node in self.nodes.values()),
            "memory_usage_mb": sum(
                node.memory_usage_mb for node in self.nodes.values()
            ),
        }

    def dashboard(self, scope: ClusterScope) -> dict[str, Any]:
        self._require(scope, "read")
        return {
            "sections": [
                "Cluster Overview",
                "Nodes",
                "Instances",
                "Queues",
                "Resources",
                "Health",
                "Recovery",
                "Telemetry",
                "Statistics",
            ],
            "clusters": [
                serialize(item) for item in self._scope_values(self.clusters, scope)
            ],
            "nodes": [
                serialize(item) for item in self._scope_values(self.nodes, scope)
            ],
            "instances": [
                serialize(item) for item in self._scope_values(self.instances, scope)
            ],
            "queues": {
                "browser_queue": len(self._queue),
                "priority_queue": sum(item.priority > 0 for item in self._queue),
                "workspace_queue": len(
                    {
                        (item.tenant, item.workspace)
                        for item in self._queue
                    }
                ),
                "account_queue": len(
                    {item.account_reference for item in self._queue}
                ),
                "retry_queue": sum(item.attempts > 0 for item in self._queue),
                "delayed_queue": 0,
                "maximum_parallel_launches": (
                    self.resources.maximum_parallel_launches
                ),
                "depth": len(self._queue),
            },
            "resources": serialize(self.resources),
            "health": self.health(scope),
            "recovery": [serialize(item) for item in self.recoveries],
            "telemetry": dict(self.metrics.values),
            "statistics": self.statistics(scope),
        }

    @staticmethod
    def _scope_values(values: dict[str, Any], scope: ClusterScope) -> list[Any]:
        return [
            item
            for item in values.values()
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def _refresh_metrics(self) -> None:
        self.metrics.set("tiktok_browser_cluster_nodes", len(self.nodes))
        self.metrics.set("tiktok_browser_cluster_instances", len(self.instances))
        self.metrics.set(
            "tiktok_browser_cluster_running",
            sum(
                item.status is InstanceStatus.RUNNING
                for item in self.instances.values()
            ),
        )
        self.metrics.set("tiktok_browser_cluster_queue", len(self._queue))
        self.metrics.set(
            "tiktok_browser_cluster_cpu_usage",
            sum(node.cpu_usage for node in self.nodes.values()),
        )
        self.metrics.set(
            "tiktok_browser_cluster_memory_usage",
            sum(node.memory_usage_mb for node in self.nodes.values()),
        )
