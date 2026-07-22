"""Offline regression tests for the backward-compatible Plugin SDK foundation."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from tkai.ai import DoctorService, DoctorStatus
from tkai.ai.cli_service import AICommandService
from tkai.commands import ai as ai_commands
from tkai.core.exceptions import PluginError
from tkai.observability import EventBus, EventDispatcher, MetricsAdapter
from tkai.plugins import Hook, PluginManager, PluginMetadata

runner = CliRunner()


class SDKPlugin:
    """Small local SDK plugin for lifecycle and stable hook order coverage."""

    def __init__(self, name: str, calls: list[str], *, fail: bool = False) -> None:
        self.name = name
        self.calls = calls
        self.fail = fail

    def initialize(self) -> None:
        self.calls.append(f"init:{self.name}")

    def shutdown(self) -> None:
        self.calls.append(f"stop:{self.name}")

    def on_hook(self, hook: Hook, payload: dict[str, object]) -> None:
        if self.fail:
            raise RuntimeError("isolated")
        self.calls.append(f"{hook.value}:{self.name}:{payload['request']}")


def metadata(name: str, *, priority: int = 0, enabled: bool = True) -> PluginMetadata:
    """Build compact immutable SDK metadata for local tests."""
    return PluginMetadata(
        name,
        "1.0",
        capabilities=frozenset({"hooks"}),
        priority=priority,
        enabled=enabled,
    )


def test_metadata_registry_lifecycle_enable_disable_and_events() -> None:
    calls: list[str] = []
    bus = EventBus()
    metrics = MetricsAdapter()
    bus.subscribe(EventDispatcher([metrics]).dispatch)
    manager = PluginManager(event_bus=bus)
    plugin = SDKPlugin("primary", calls)

    manager.register_sdk(plugin, metadata("primary", enabled=False))
    assert calls == ["init:primary"]
    assert not manager.registry.enabled("primary")
    manager.enable("primary")
    manager.disable("primary")
    manager.unload_sdk("primary")

    assert [event.name for event in manager.events] == [
        "PluginLoaded",
        "PluginEnabled",
        "PluginDisabled",
        "PluginUnloaded",
    ]
    assert metrics.counts["PluginLoaded"] == 1
    assert calls[-1] == "stop:primary"


def test_hooks_are_priority_ordered_and_plugin_failures_are_isolated() -> None:
    calls: list[str] = []
    manager = PluginManager()
    manager.register_sdk(SDKPlugin("low", calls), metadata("low", priority=1))
    manager.register_sdk(SDKPlugin("high", calls), metadata("high", priority=2))
    manager.register_sdk(
        SDKPlugin("bad", calls, fail=True), metadata("bad", priority=3)
    )

    manager.dispatch(Hook.BEFORE_REQUEST, {"request": "one"})

    assert calls[3:] == ["BeforeRequest:high:one", "BeforeRequest:low:one"]
    assert manager.events[-1].name == "PluginFailed"


def test_doctor_and_cli_plugin_summary(monkeypatch) -> None:
    calls: list[str] = []
    manager = PluginManager()
    manager.register_sdk(SDKPlugin("primary", calls), metadata("primary"))
    report = DoctorService(plugins=manager).run()
    check = next(item for item in report.checks if item.name == "plugins.registry")
    assert check.status is DoctorStatus.PASS
    assert check.detail["enabled"] == ["primary"]

    monkeypatch.setattr(ai_commands, "_service", AICommandService(plugins=manager))
    text = runner.invoke(ai_commands.app, ["plugins"])
    structured = runner.invoke(ai_commands.app, ["plugins", "--json"])
    invalid = runner.invoke(ai_commands.app, ["plugins", "--invalid"])
    assert text.exit_code == 0
    assert '"name": "primary"' in text.stdout
    assert structured.exit_code == 0
    assert '"capabilities": ["hooks"]' in structured.stdout
    assert invalid.exit_code == 2


def test_invalid_metadata_and_duplicate_registration_are_rejected() -> None:
    with pytest.raises(ValueError):
        PluginMetadata("", "1")
    manager = PluginManager()
    manager.register_sdk(SDKPlugin("one", []), metadata("one"))
    with pytest.raises(PluginError):
        manager.register_sdk(SDKPlugin("one", []), metadata("one"))
