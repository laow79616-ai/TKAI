"""Offline cache hit, miss, expiry, and key-builder benchmarks."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from _runner import BenchmarkResult, render, run

from tkai.cache import CacheEntry, CacheKeyBuilder, CacheManager


def run_benchmark(iterations: int = 10_000) -> list[BenchmarkResult]:
    """Measure cache operations without providers, transports, or network access."""
    manager = CacheManager()
    manager.set(CacheEntry("hit", "value"))
    key_builder = CacheKeyBuilder()
    expired = CacheEntry(
        "expired", "value", expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)
    )
    manager.set(expired)
    return [
        run("cache.hit", lambda: manager.get("hit"), iterations),
        run("cache.miss", lambda: manager.get("missing"), iterations),
        run("cache.ttl_expiration", lambda: manager.get("expired"), iterations),
        run(
            "cache.key_builder",
            lambda: key_builder.build(
                provider="local", model="model", prompt={"text": "hello"}
            ),
            iterations,
        ),
    ]


if __name__ == "__main__":
    print(render(run_benchmark()))
