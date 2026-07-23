"""Mixed bounded execution checks for the Sprint-2 local composition benchmark."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from benchmarks.combined_runtime import CombinedRuntimeBenchmark


def test_combined_runtime_async_and_threaded_requests_do_not_share_state() -> None:
    """Run isolated local compositions from bounded tasks in bounded worker threads."""
    workers = 4
    tasks_per_worker = 5

    def worker(worker_id: int) -> list[tuple[str, dict[str, int]]]:
        async def execute() -> list[tuple[str, dict[str, int]]]:
            async def request(task_id: int) -> tuple[str, dict[str, int]]:
                benchmark = CombinedRuntimeBenchmark()
                benchmark.run(iterations=1)
                request_id = f"{worker_id}:{task_id}"
                return request_id, dict(benchmark.stage_counts)

            return list(
                await asyncio.gather(
                    *(request(task_id) for task_id in range(tasks_per_worker))
                )
            )

        return asyncio.run(execute())

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = [
            future.result(timeout=15)
            for future in [
                executor.submit(worker, worker_id) for worker_id in range(workers)
            ]
        ]

    flattened = [item for group in results for item in group]
    assert {request_id for request_id, _counts in flattened} == {
        f"{worker_id}:{task_id}"
        for worker_id in range(workers)
        for task_id in range(tasks_per_worker)
    }
    assert all(sum(counts.values()) == 7 for _request_id, counts in flattened)
