"""Offline asyncio reliability checks using only local backend primitives."""

from __future__ import annotations

import asyncio

import pytest

from tkai.distributed import LocalBackend
from tkai.telemetry import CorrelationContext, LocalExporter, Metric


def test_async_local_backend_tasks_are_isolated_and_cleaned_up() -> None:
    """Concurrent local async calls retain each task's independent request context."""

    async def exercise() -> None:
        backend = LocalBackend()

        async def operation(number: int) -> CorrelationContext:
            context = CorrelationContext(
                request_id=f"request-{number}", trace_id=f"trace-{number}"
            )
            await backend.aset(context.request_id or "", number)
            assert await backend.aget(context.request_id or "") == number
            assert await backend.adelete(context.request_id or "")
            return context

        contexts = await asyncio.gather(*(operation(number) for number in range(48)))
        assert {context.request_id for context in contexts} == {
            f"request-{number}" for number in range(48)
        }
        assert all(context.request_id != context.trace_id for context in contexts)

    asyncio.run(exercise())


def test_async_cancellation_and_timeout_release_local_waiters() -> None:
    """Await cancelled work and timeout paths so no task remains pending."""

    async def exercise() -> None:
        gate = asyncio.Event()
        cancelled = asyncio.create_task(gate.wait())
        cancelled.cancel()
        with pytest.raises(asyncio.CancelledError):
            await cancelled
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(gate.wait(), timeout=0.01)
        assert cancelled.done()

    asyncio.run(exercise())


def test_async_exporter_failure_does_not_contaminate_independent_tasks() -> None:
    """Successful tasks complete even when one local task raises independently."""

    async def exercise() -> None:
        exporter = LocalExporter()
        await exporter.async_start()

        async def record(number: int) -> int:
            if number == 3:
                raise ValueError("local failure")
            await exporter.async_export_metric(Metric("async.stress", number))
            return number

        results = await asyncio.gather(
            *(record(number) for number in range(8)), return_exceptions=True
        )
        assert sum(isinstance(result, ValueError) for result in results) == 1
        assert {result for result in results if isinstance(result, int)} == set(
            range(8)
        ) - {3}
        assert len(exporter.metrics) == 7
        await exporter.async_stop()
        assert not exporter.health()

    asyncio.run(exercise())
