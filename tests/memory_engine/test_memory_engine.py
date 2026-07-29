from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from memory_engine import (
    EnterpriseAIMemoryEngine,
    LifecycleState,
    MemoryScope,
    MemoryType,
    SearchQuery,
)
from memory_engine.api import register_memory_routes
from memory_engine.compression import MemoryCompressor
from memory_engine.dashboard import SECTIONS
from memory_engine.retention import RetentionPolicy

PERMISSIONS = {
    "memory:read",
    "memory:write",
    "memory:delete",
    "memory:retention",
}


def configured(
    *, cache_limit: int = 10, policy: RetentionPolicy | None = None
) -> tuple[EnterpriseAIMemoryEngine, MemoryScope]:
    engine = EnterpriseAIMemoryEngine(cache_limit=cache_limit, retention_policy=policy)
    scope = MemoryScope("tenant-a", "workspace-a", "alice")
    engine.security.grant(scope, PERMISSIONS)
    return engine, scope


def payload(
    memory_id: str = "memory-1",
    *,
    content: str = "Enterprise agent remembers customer preferences",
    memory_type: str = "semantic",
) -> dict[str, object]:
    return {
        "id": memory_id,
        "namespace": "agents/support",
        "type": memory_type,
        "source": "agent-runtime",
        "content": content,
        "metadata": {"department": "support", "secret_ref": "secret://memory/key"},
        "priority": 80,
    }


def test_memory_object_types_lifecycle_metrics_and_dashboard() -> None:
    engine, scope = configured()
    memory = engine.create(payload(), scope)

    assert memory.type is MemoryType.SEMANTIC
    assert memory.state is LifecycleState.INDEXED
    assert memory.to_dict()["tenant"] == scope.tenant
    assert engine.get(memory.id, scope).state is LifecycleState.RETRIEVED
    updated = engine.update(memory.id, {"content": "updated preference"}, scope)
    assert updated.updated >= updated.created
    assert set(SECTIONS) <= set(engine.dashboard(scope)["sections"])
    assert engine.metrics.snapshot()["memory_writes_total"] == 2

    engine.delete(memory.id, scope)
    assert memory.state is LifecycleState.DELETED
    assert engine.metrics.snapshot()["memory_objects_total"] == 0


@pytest.mark.parametrize(
    "memory_type",
    ["working", "short_term", "long_term", "semantic", "episodic", "session", "shared"],
)
def test_all_memory_types(memory_type: str) -> None:
    engine, scope = configured()
    memory = engine.create(payload(memory_type, memory_type=memory_type), scope)
    assert memory.type.value == memory_type


def test_keyword_similarity_hybrid_filters_top_k_and_threshold() -> None:
    engine, scope = configured()
    engine.create(payload("one", content="alpha beta"), scope)
    second = payload("two", content="alpha gamma")
    second["metadata"] = {"department": "engineering"}
    engine.create(second, scope)

    keyword = engine.search(SearchQuery("beta", mode="keyword", threshold=0.5), scope)
    assert [result.memory.id for result in keyword] == ["one"]
    similarity = engine.search(SearchQuery("alpha", mode="similarity", top_k=1), scope)
    assert len(similarity) == 1
    hybrid = engine.search(
        SearchQuery(
            "alpha",
            namespace="agents/support",
            metadata={"department": "engineering"},
        ),
        scope,
    )
    assert [result.memory.id for result in hybrid] == ["two"]


def test_cache_eviction_limits_hits_and_misses() -> None:
    engine, scope = configured(cache_limit=1)
    first = engine.create(payload("one"), scope)
    engine.create(payload("two"), scope)
    assert engine.cache.snapshot()["evictions"] == 1
    assert engine.get(first.id, scope) is first
    metrics = engine.metrics.snapshot()
    assert metrics["memory_cache_misses_total"] == 1
    assert engine.get(first.id, scope) is first
    assert engine.metrics.snapshot()["memory_cache_hits_total"] == 1


def test_ttl_cleanup_archive_compaction_and_compression() -> None:
    engine, scope = configured(policy=RetentionPolicy(default_ttl=1))
    expired = engine.create(payload("expired"), scope)
    expired.updated = datetime.now(UTC) - timedelta(seconds=2)
    assert engine.cleanup(scope) == 1
    assert expired.state is LifecycleState.ARCHIVED
    assert engine.metrics.snapshot()["memory_expired_total"] == 1

    engine.create(payload("duplicate-a", content="same"), scope)
    engine.create(payload("duplicate-b", content="same"), scope)
    assert engine.compact(scope) == 1

    compressor = MemoryCompressor()
    chunk = compressor.compress_chunk("repeat " * 100)
    metadata = compressor.compress_metadata({"kind": "test"})
    assert compressor.decompress_chunk(chunk) == "repeat " * 100
    assert compressor.decompress_metadata(metadata) == {"kind": "test"}


def test_namespace_tenant_workspace_owner_rbac_secrets_and_audit() -> None:
    engine, scope = configured()
    memory = engine.create(payload(), scope)
    assert engine.namespaces.list(scope) == ("agents/support",)
    with pytest.raises(PermissionError):
        engine.get(memory.id, MemoryScope("tenant-b", "workspace-a", "alice"))
    with pytest.raises(PermissionError):
        engine.get(memory.id, MemoryScope("tenant-a", "workspace-b", "alice"))
    with pytest.raises(ValueError):
        engine.create({**payload("unsafe"), "metadata": {"secret": "plaintext"}}, scope)
    assert any(event["action"] == "memory:created" for event in engine.security.audit)


class App:
    def __init__(self) -> None:
        self.routes: set[tuple[str, str]] = set()

    def add_api_route(
        self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        self.routes.update((method, path) for method in methods)


def test_api_and_metrics_contract() -> None:
    app = App()
    engine, _ = configured()
    register_memory_routes(app, engine)
    for path in (
        "/memory",
        "/memory/search",
        "/memory/cache",
        "/memory/retention",
        "/memory/namespaces",
    ):
        assert any(route_path == path for _, route_path in app.routes)
    for metric in (
        "memory_objects_total",
        "memory_reads_total",
        "memory_writes_total",
        "memory_cache_hits_total",
        "memory_cache_misses_total",
        "memory_retrieval_total",
        "memory_expired_total",
    ):
        assert metric in engine.metrics.render_prometheus()
