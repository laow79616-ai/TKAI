"""Offline local quota consumption and reset benchmarks."""

from __future__ import annotations

from _runner import BenchmarkResult, render, run

from tkai.rate_limit import (
    FixedWindowStrategy,
    RateLimitManager,
    RateLimitSnapshot,
    RateLimitStrategy,
    SlidingWindowStrategy,
)


def _manager(strategy: RateLimitStrategy) -> RateLimitManager:
    manager = RateLimitManager(strategy=strategy)
    manager.register(RateLimitSnapshot("local"))
    return manager


def run_benchmark(iterations: int = 1_000) -> list[BenchmarkResult]:
    """Measure unbounded local quota mechanics, including reset cost."""
    sliding = _manager(SlidingWindowStrategy())
    fixed = _manager(FixedWindowStrategy())
    return [
        run("rate_limit.sliding_consume", lambda: sliding.consume("local"), iterations),
        run("rate_limit.fixed_consume", lambda: fixed.consume("local"), iterations),
        run("rate_limit.sliding_reset", lambda: sliding.reset("local"), iterations),
        run("rate_limit.fixed_reset", lambda: fixed.reset("local"), iterations),
    ]


if __name__ == "__main__":
    print(render(run_benchmark()))
