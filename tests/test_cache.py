"""Offline regression tests for the optional local cache framework."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from typer.testing import CliRunner

from tkai.ai import DoctorService, DoctorStatus
from tkai.ai.cli_service import AICommandService
from tkai.cache import (
    CacheEntry,
    CacheKeyBuilder,
    CacheManager,
    CacheRegistry,
    InMemoryBackend,
    NoCache,
)
from tkai.commands import ai as ai_commands
from tkai.observability import EventBus, EventDispatcher, MetricsAdapter

runner = CliRunner()


class MutableClock:
    """Deterministic UTC clock used for local cache expiration tests."""

    def __init__(self) -> None:
        self.value = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.value

    def advance(self, seconds: int) -> None:
        self.value += timedelta(seconds=seconds)


def test_entry_validation_access_metadata_and_serialization() -> None:
    now = datetime.now(timezone.utc)
    entry = CacheEntry("key", {"answer": 1}, ttl=10, created_at=now)

    assert entry.expires_at == now + timedelta(seconds=10)
    assert entry.accessed(now).hit_count == 1
    assert entry.to_dict()["created_at"].endswith("+00:00")
    with pytest.raises(ValueError):
        CacheEntry("", "value")
    with pytest.raises(ValueError):
        CacheEntry("key", "value", ttl=-1)


def test_memory_backend_ttl_hit_miss_eviction_and_shared_events() -> None:
    clock = MutableClock()
    bus = EventBus()
    metrics = MetricsAdapter()
    bus.subscribe(EventDispatcher([metrics]).dispatch)
    backend = InMemoryBackend(event_bus=bus, clock=clock)
    backend.set(CacheEntry("key", "value", ttl=2, created_at=clock()))

    assert backend.get("key") is not None
    assert backend.get("missing") is None
    clock.advance(2)
    assert backend.get("key") is None
    backend.set(CacheEntry("evict", "value", created_at=clock()))
    assert backend.delete("evict")
    statistics = backend.statistics()
    assert (
        statistics.hits,
        statistics.misses,
        statistics.expired,
        statistics.evicted,
    ) == (1, 2, 1, 1)
    assert metrics.counts["CacheHit"] == 1
    assert metrics.counts["CacheMiss"] == 1
    assert metrics.counts["CacheExpired"] == 1
    assert metrics.counts["CacheEvicted"] == 1


def test_registry_key_builder_and_optional_read_through_runtime_flow() -> None:
    registry = CacheRegistry()
    backend = InMemoryBackend()
    registry.register("memory", backend)
    manager = CacheManager(registry=registry)
    builder = CacheKeyBuilder()
    key = builder.build(
        provider="openai",
        model="test",
        prompt={"x": 1},
        parameters={"temperature": 0},
    )
    same = builder.build(
        provider="openai",
        model="test",
        prompt={"x": 1},
        parameters={"temperature": 0},
    )
    calls: list[str] = []

    assert key == same
    assert manager.get_or_set(key, lambda: calls.append("miss") or "answer") == "answer"
    assert manager.get_or_set(key, lambda: calls.append("again") or "other") == "answer"
    assert calls == ["miss"]
    assert manager.get_or_set("none", lambda: "fresh", policy=NoCache()) == "fresh"
    assert backend.get("none") is None


def test_doctor_and_cli_cache_summary(monkeypatch) -> None:
    manager = CacheManager()
    manager.set(CacheEntry("key", "value"))
    assert manager.get("key") is not None
    report = DoctorService(cache=manager).run()
    check = next(item for item in report.checks if item.name == "cache.registry")
    assert check.status is DoctorStatus.PASS
    assert check.detail["backend_count"] == 1

    monkeypatch.setattr(ai_commands, "_service", AICommandService(cache=manager))
    text = runner.invoke(ai_commands.app, ["cache"])
    structured = runner.invoke(ai_commands.app, ["cache", "--json"])
    invalid = runner.invoke(ai_commands.app, ["cache", "--invalid"])
    assert text.exit_code == 0
    assert '"backend": "memory"' in text.stdout
    assert structured.exit_code == 0
    assert '"entries": 1' in structured.stdout
    assert invalid.exit_code == 2
