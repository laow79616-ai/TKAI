"""Offline regression tests for explicit local multi-region routing."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest
from typer.testing import CliRunner

from tkai.ai import DoctorService, DoctorStatus
from tkai.ai.cli_service import AICommandService
from tkai.commands import ai as ai_commands
from tkai.multiregion import (
    MultiRegionManager,
    MultiRegionPolicyAdapter,
    MultiRegionRuntimeAdapter,
    NoRegionAvailableError,
    Region,
    RegionPolicy,
    RegionRole,
)
from tkai.observability import EventBus
from tkai.policy import PolicyContext, PolicyStage


def test_model_registry_topology_and_stable_selection() -> None:
    manager = MultiRegionManager()
    manager.register_region(Region("west", priority=1, latency_estimate_ms=50))
    manager.register_region(Region("east", priority=1, latency_estimate_ms=30))
    manager.topology.set_role("west", RegionRole.PRIMARY)
    manager.topology.set_role("east", RegionRole.PRIMARY)
    decision = manager.select_region()
    assert decision.selected_region == "east"
    assert manager.registry.snapshot()[0].to_dict()["updated_at"].endswith("+00:00")
    manager.disable("east")
    assert manager.select_region().selected_region == "west"


def test_policy_breaker_fallback_and_failure_isolation() -> None:
    manager = MultiRegionManager(event_bus=EventBus())
    manager.event_bus.subscribe(lambda _event: (_ for _ in ()).throw(RuntimeError()))
    manager.register_region(Region("open", metadata={"breaker_open": True}))
    manager.register_region(Region("backup", healthy=False))
    assert manager.select_region().selected_region == "backup"
    assert manager.events
    manager.policy = RegionPolicy(allow_fallback=False)
    manager.router.policy = manager.policy
    with pytest.raises(NoRegionAvailableError):
        manager.select_region()


def test_registry_thread_safety_runtime_policy_doctor_and_cli(monkeypatch) -> None:
    manager = MultiRegionManager()
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(
            executor.map(
                lambda number: manager.register_region(Region(f"r{number}")), range(10)
            )
        )
    assert [region.region_id for region in manager.registry.list()] == [
        f"r{number}" for number in range(10)
    ]
    runtime = MultiRegionRuntimeAdapter(manager)
    assert runtime.select_region().selected_region == "r0"
    policy = MultiRegionPolicyAdapter(manager)
    context = PolicyContext(PolicyStage.BEFORE_ROUTING)
    policy.apply(context)
    assert context.data["region_decision"].selected_region == "r0"
    check = next(
        item
        for item in DoctorService(multiregion=manager).run().checks
        if item.name == "multiregion"
    )
    assert check.status is DoctorStatus.PASS
    monkeypatch.setattr(ai_commands, "_service", AICommandService(multiregion=manager))
    result = CliRunner().invoke(ai_commands.app, ["multiregion", "--json"])
    assert result.exit_code == 0
    assert '"regions"' in result.stdout
