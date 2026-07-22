"""Offline ProviderRuntime request-scope benchmark with a no-op transport."""

from __future__ import annotations

import asyncio
import time

from _runner import BenchmarkResult, render

from tkai.ai.runtime import AsyncTransport, OwnershipPolicy, ProviderRuntime


class _NoopTransport:
    """Minimal transport used only to measure runtime scope overhead offline."""

    async def request(self, method: str, url: str, **kwargs: object) -> object:
        return {"method": method, "url": url, **kwargs}

    def stream(self, method: str, url: str, **kwargs: object):
        raise AssertionError("stream is not used by this benchmark")

    async def close(self) -> None:
        return None

    def health_check(self) -> bool:
        return True


async def _measure(iterations: int) -> BenchmarkResult:
    transport: AsyncTransport = _NoopTransport()
    runtime = ProviderRuntime(transport, ownership=OwnershipPolicy.EXTERNALLY_OWNED)
    samples: list[int] = []
    cpu_start = time.process_time_ns()
    wall_start = time.perf_counter_ns()
    for _ in range(iterations):
        start = time.perf_counter_ns()
        async with runtime.request_scope():
            pass
        samples.append(time.perf_counter_ns() - start)
    wall_elapsed = time.perf_counter_ns() - wall_start
    cpu_elapsed = time.process_time_ns() - cpu_start
    milliseconds = sorted(sample / 1_000_000 for sample in samples)
    wall_seconds = wall_elapsed / 1_000_000_000
    return BenchmarkResult(
        "provider_runtime.request_scope",
        iterations,
        iterations / wall_seconds if wall_seconds else float("inf"),
        sum(milliseconds) / len(milliseconds),
        milliseconds[len(milliseconds) // 2],
        milliseconds[max(0, int(len(milliseconds) * 0.95 + 0.5) - 1)],
        milliseconds[max(0, int(len(milliseconds) * 0.99 + 0.5) - 1)],
        milliseconds[-1],
        cpu_elapsed / 1_000_000,
        wall_elapsed / 1_000_000,
    )


def run_benchmark(iterations: int = 10_000) -> list[BenchmarkResult]:
    """Measure request-scope lifecycle overhead on one local event loop."""
    return [asyncio.run(_measure(iterations))]


if __name__ == "__main__":
    print(render(run_benchmark()))
