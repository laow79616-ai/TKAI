"""Bounded concurrent validation for V1.3 telemetry and scheduler integration."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from tkai.runtime_scheduler import RuntimeScheduler
from tkai.telemetry import Metric, TelemetryManager


def test_v13_scheduler_decisions_and_telemetry_records_remain_consistent() -> None:
    """Concurrent local decisions never invoke providers or drop metric records."""
    telemetry = TelemetryManager()
    telemetry.start()
    scheduler = RuntimeScheduler(telemetry=telemetry)
    scheduler.register("one", latency_ms=1)
    scheduler.register("two", latency_ms=2)

    def operate(number: int) -> str | None:
        telemetry.record(Metric("v13.scheduler", number))
        return scheduler.schedule().provider

    with ThreadPoolExecutor(max_workers=8) as executor:
        selected = list(executor.map(operate, range(48)))

    assert set(selected) <= {"one", "two"}
    assert len(telemetry.metrics.snapshot()) == 96
    telemetry.stop()
