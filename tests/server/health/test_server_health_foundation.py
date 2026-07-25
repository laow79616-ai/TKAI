"""Offline coverage for the Marketplace Server Health Foundation."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError

import pytest

from server.health import (
    HealthCheck,
    HealthCheckId,
    HealthClosedError,
    HealthConflictError,
    HealthEventType,
    HealthNotFoundError,
    HealthResult,
    HealthSeverity,
    HealthStatus,
    ReferenceHealthService,
    ReferenceHealthStorage,
)


def _check(identifier: str = "check-1") -> HealthCheck:
    return HealthCheck(
        identifier,
        check_id=HealthCheckId(identifier),
        metadata={"scope": "reference"},
    )


def _result(
    identifier: str = "check-1", status: HealthStatus = HealthStatus.HEALTHY
) -> HealthResult:
    return HealthResult(
        HealthCheckId(identifier),
        status,
        HealthSeverity.INFO,
        metadata={"scope": "reference"},
    )


def test_models_are_immutable_defensive_and_json_safe() -> None:
    values = {"scope": "reference"}
    check = HealthCheck("storage", metadata=values)
    values["scope"] = "changed"
    result = _result("storage", HealthStatus.DEGRADED)

    assert str(check.check_id) == "storage"
    assert check.metadata["scope"] == "reference"
    with pytest.raises(TypeError):
        check.metadata["extra"] = "value"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        result.message = "changed"  # type: ignore[misc]
    assert json.loads(json.dumps(result.to_dict()))["status"] == "degraded"


def test_register_update_unregister_and_duplicate_rejection() -> None:
    service = ReferenceHealthService()
    service.register_check(_check())
    service.update_result(_result(status=HealthStatus.UNHEALTHY))

    assert service.statistics().unhealthy == 1
    assert service.get_check(HealthCheckId("check-1")).name == "check-1"
    with pytest.raises(HealthConflictError):
        service.register_check(_check())
    assert service.unregister_check(HealthCheckId("check-1")).name == "check-1"
    with pytest.raises(HealthNotFoundError):
        service.update_result(_result())


def test_statistics_snapshot_events_and_ordering_are_deterministic() -> None:
    service = ReferenceHealthService()
    service.register_check(_check("b"))
    service.register_check(_check("a"))
    service.update_result(_result("a", HealthStatus.HEALTHY))
    service.update_result(_result("b", HealthStatus.DEGRADED))
    snapshot = service.snapshot()

    assert tuple(check.name for check in snapshot.checks) == ("a", "b")
    assert (snapshot.statistics.healthy, snapshot.statistics.degraded) == (1, 1)
    assert tuple(event.sequence for event in snapshot.events) == (1, 2, 3, 4)
    assert snapshot.events[-1].event_type is HealthEventType.RESULT_UPDATED
    assert json.loads(json.dumps(snapshot.to_dict()))["statistics"]["total_checks"] == 2


def test_clear_close_and_final_reads_are_safe_and_idempotent() -> None:
    service = ReferenceHealthService()
    service.register_check(_check())
    service.clear()
    service.close()
    service.close()
    snapshot = service.snapshot()

    assert snapshot.closed is True
    assert snapshot.checks == () and snapshot.results == ()
    assert snapshot.events[-1].event_type is HealthEventType.CLOSED
    assert service.statistics().closed is True
    with pytest.raises(HealthClosedError):
        service.list_checks()
    with pytest.raises(HealthClosedError):
        service.register_check(_check("after-close"))


def test_thread_safety_and_instance_isolation_are_bounded() -> None:
    service = ReferenceHealthService(ReferenceHealthStorage())

    def register(index: int) -> str:
        identifier = f"check-{index:02d}"
        service.register_check(_check(identifier))
        service.update_result(_result(identifier, HealthStatus.HEALTHY))
        return identifier

    with ThreadPoolExecutor(max_workers=8) as executor:
        identifiers = tuple(executor.map(register, range(32)))

    other = ReferenceHealthService()
    assert len(set(identifiers)) == 32
    assert service.statistics().healthy == 32
    assert other.snapshot().checks == ()
    assert tuple(event.sequence for event in service.events()) == tuple(range(1, 65))
