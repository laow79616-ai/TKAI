"""Enterprise AI Memory Engine facade."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from .cache import MemoryCache
from .compression import MemoryCompressor
from .index import MemoryIndex
from .metrics import MemoryMetrics
from .models import (
    LifecycleState,
    MemoryObject,
    MemoryScope,
    MemoryType,
    SearchQuery,
    SearchResult,
)
from .namespace import NamespaceRegistry
from .retention import RetentionManager, RetentionPolicy
from .security import MemorySecurity


class EnterpriseAIMemoryEngine:
    def __init__(
        self,
        *,
        cache_limit: int = 1000,
        retention_policy: RetentionPolicy | None = None,
    ) -> None:
        self.metrics = MemoryMetrics()
        self.security = MemorySecurity()
        self.cache = MemoryCache(self.metrics, cache_limit)
        self.index = MemoryIndex()
        self.namespaces = NamespaceRegistry()
        self.retention = RetentionManager(retention_policy)
        self.compression = MemoryCompressor()
        self._objects: dict[str, MemoryObject] = {}
        self._archive: dict[str, MemoryObject] = {}

    def create(self, payload: dict[str, Any], scope: MemoryScope) -> MemoryObject:
        self.security.require(scope, "memory:write")
        self.security.validate_secrets(payload.get("metadata", {}))
        now = datetime.now(UTC)
        memory = MemoryObject(
            id=str(payload.get("id") or uuid4()),
            namespace=str(payload["namespace"]),
            tenant=scope.tenant,
            workspace=scope.workspace,
            owner=scope.owner,
            type=MemoryType(str(payload["type"])),
            source=str(payload["source"]),
            content=str(payload["content"]),
            created=now,
            updated=now,
            ttl=self.retention.ttl_for(
                int(payload["ttl"]) if payload.get("ttl") is not None else None
            ),
            metadata=dict(payload.get("metadata", {})),
            priority=int(payload.get("priority", 50)),
        )
        if not 0 <= memory.priority <= 100:
            raise ValueError("Priority must be between zero and 100.")
        self._objects[memory.id] = memory
        self.namespaces.register(scope, memory.namespace)
        self._index(memory)
        self.cache.write(memory)
        self.metrics.increment("memory_writes_total")
        self.metrics.set("memory_objects_total", len(self._objects))
        self.security.record(scope, "memory:created", memory_id=memory.id)
        return memory

    def update(
        self, memory_id: str, payload: dict[str, Any], scope: MemoryScope
    ) -> MemoryObject:
        self.security.require(scope, "memory:write")
        memory = self._get_scoped(memory_id, scope)
        self.security.validate_secrets(payload.get("metadata", {}))
        if "content" in payload:
            memory.content = str(payload["content"])
        if "metadata" in payload:
            memory.metadata = dict(payload["metadata"])
        if "ttl" in payload:
            value = payload["ttl"]
            memory.ttl = self.retention.ttl_for(
                int(value) if value is not None else None
            )
        if "priority" in payload:
            memory.priority = int(payload["priority"])
            if not 0 <= memory.priority <= 100:
                raise ValueError("Priority must be between zero and 100.")
        memory.updated = datetime.now(UTC)
        memory.state = LifecycleState.UPDATED
        self._index(memory)
        self.cache.write(memory)
        self.metrics.increment("memory_writes_total")
        self.security.record(scope, "memory:updated", memory_id=memory.id)
        return memory

    def get(self, memory_id: str, scope: MemoryScope) -> MemoryObject:
        self.security.require(scope, "memory:read")
        memory = self.cache.read(memory_id)
        if memory is None:
            memory = self._get_scoped(memory_id, scope)
            self.cache.write(memory)
        else:
            self.security.isolate(scope, memory)
        if self.retention.expired(memory):
            self._expire(memory)
            raise KeyError(memory_id)
        memory.state = LifecycleState.RETRIEVED
        self.metrics.increment("memory_reads_total")
        self.security.record(scope, "memory:retrieved", memory_id=memory.id)
        return memory

    def list(
        self, scope: MemoryScope, namespace: str | None = None
    ) -> tuple[MemoryObject, ...]:
        self.security.require(scope, "memory:read")
        return tuple(
            memory
            for memory in self._objects.values()
            if memory.tenant == scope.tenant
            and memory.workspace == scope.workspace
            and (memory.owner == scope.owner or memory.type is MemoryType.SHARED)
            and (namespace is None or memory.namespace == namespace)
            and not memory.expired()
        )

    def search(
        self, query: SearchQuery, scope: MemoryScope
    ) -> tuple[SearchResult, ...]:
        self.security.require(scope, "memory:read")
        candidates = {memory.id for memory in self.list(scope)}
        results = self.index.search(query, candidates)
        self.metrics.increment("memory_retrieval_total")
        self.metrics.increment("memory_reads_total", len(results))
        for result in results:
            result.memory.state = LifecycleState.RETRIEVED
        self.security.record(scope, "memory:search", results=len(results))
        return results

    def delete(self, memory_id: str, scope: MemoryScope) -> None:
        self.security.require(scope, "memory:delete")
        memory = self._get_scoped(memory_id, scope)
        memory.state = LifecycleState.DELETED
        self._objects.pop(memory_id)
        self.index.remove(memory_id)
        self.cache.evict(memory_id)
        self.metrics.set("memory_objects_total", len(self._objects))
        self.security.record(scope, "memory:deleted", memory_id=memory_id)

    def archive(self, memory_id: str, scope: MemoryScope) -> MemoryObject:
        self.security.require(scope, "memory:retention")
        memory = self._get_scoped(memory_id, scope)
        memory.state = LifecycleState.ARCHIVED
        self._archive[memory.id] = memory
        self._objects.pop(memory.id)
        self.index.remove(memory.id)
        self.cache.evict(memory.id)
        self.metrics.set("memory_objects_total", len(self._objects))
        self.security.record(scope, "memory:archived", memory_id=memory.id)
        return memory

    def cleanup(self, scope: MemoryScope, now: datetime | None = None) -> int:
        self.security.require(scope, "memory:retention")
        expired = [
            memory
            for memory in self._objects.values()
            if memory.tenant == scope.tenant
            and memory.workspace == scope.workspace
            and memory.expired(now)
            and memory.priority < self.retention.policy.cleanup_priority_below
        ]
        for memory in expired:
            self._expire(memory)
        self.security.record(scope, "memory:cleanup", count=len(expired))
        return len(expired)

    def compact(self, scope: MemoryScope) -> int:
        self.security.require(scope, "memory:retention")
        scoped = list(self.list(scope))
        retained = {memory.id for memory in self.retention.compact(scoped)}
        duplicates = [memory for memory in scoped if memory.id not in retained]
        for memory in duplicates:
            self.archive(memory.id, scope)
        self.security.record(scope, "memory:compacted", count=len(duplicates))
        return len(duplicates)

    def dashboard(self, scope: MemoryScope) -> dict[str, Any]:
        memories = self.list(scope)
        usage = sum(
            self.compression.optimized_size(memory.content, memory.metadata)
            for memory in memories
        )
        return {
            "sections": (
                "Memory Overview",
                "Namespaces",
                "Usage",
                "Retention",
                "Cache",
                "Retrieval",
                "Metrics",
            ),
            "overview": {"objects": len(memories), "archived": len(self._archive)},
            "namespaces": self.namespaces.list(scope),
            "usage": {"optimized_bytes": usage},
            "retention": {
                "default_ttl": self.retention.policy.default_ttl,
                "archive_expired": self.retention.policy.archive_expired,
            },
            "cache": self.cache.snapshot(),
            "retrieval": {"indexed": len(memories)},
            "metrics": self.metrics.snapshot(),
        }

    def _get_scoped(self, memory_id: str, scope: MemoryScope) -> MemoryObject:
        memory = self._objects[memory_id]
        self.security.isolate(scope, memory)
        return memory

    def _index(self, memory: MemoryObject) -> None:
        self.index.add(memory)
        memory.state = LifecycleState.INDEXED

    def _expire(self, memory: MemoryObject) -> None:
        memory.state = LifecycleState.EXPIRED
        self._objects.pop(memory.id, None)
        self.index.remove(memory.id)
        self.cache.evict(memory.id)
        if self.retention.policy.archive_expired:
            memory.state = LifecycleState.ARCHIVED
            self._archive[memory.id] = memory
        self.metrics.increment("memory_expired_total")
        self.metrics.set("memory_objects_total", len(self._objects))
