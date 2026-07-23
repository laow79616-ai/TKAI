"""Offline V1.2 RC-1 integration, compatibility, and lifecycle baseline."""

from __future__ import annotations

import importlib
from datetime import datetime, timezone

from typer.testing import CliRunner

import tkai
from tkai.adaptive import AdaptiveRoutingManager, ProviderSignal
from tkai.ai import DoctorService
from tkai.ai.cli_service import AICommandService
from tkai.commands import ai as ai_commands
from tkai.configuration import ConfigurationManager, ConfigurationResolver
from tkai.configuration.sources.memory import MemoryConfigurationLoader
from tkai.distributed import DistributedCoordinator, Node
from tkai.multiregion import MultiRegionManager, Region
from tkai.observability import EventBus
from tkai.policy import PolicyContext, PolicyManager, PolicyStage
from tkai.retry import RetryManager, RetryPolicy
from tkai.telemetry import Metric, TelemetryManager, TelemetryPolicyAdapter


class _FailingPolicy:
    def name(self) -> str:
        return "failing"

    def priority(self) -> int:
        return 0

    def enabled(self) -> bool:
        return True

    def evaluate(self, context: PolicyContext):
        del context
        raise RuntimeError("isolated")

    def apply(self, context: PolicyContext) -> None:
        del context

    def shutdown(self) -> None:
        return None


def test_v12_public_modules_and_version_are_importable_without_side_effects() -> None:
    assert tkai.__version__ == "1.3.0rc1"
    for name in (
        "tkai.policy",
        "tkai.retry",
        "tkai.distributed",
        "tkai.telemetry",
        "tkai.adaptive",
        "tkai.multiregion",
    ):
        assert importlib.import_module(name) is not None


def test_configuration_defaults_legacy_and_explicit_overrides_remain_additive() -> None:
    defaults = ConfigurationManager(ConfigurationResolver([])).load()
    assert defaults.source == "default"
    legacy = ConfigurationManager(
        ConfigurationResolver([MemoryConfigurationLoader({"provider": {"timeout": 5}})])
    ).load()
    assert legacy.get("provider.timeout") == 5
    explicit = ConfigurationManager(
        ConfigurationResolver(
            [
                MemoryConfigurationLoader({"provider": {"timeout": 5}}),
                MemoryConfigurationLoader({"provider": {"timeout": 10}}),
            ]
        )
    ).load()
    assert explicit.get("provider.timeout") == 10


def test_optional_services_share_lifecycle_events_and_doctor_aggregation() -> None:
    bus = EventBus()
    telemetry = TelemetryManager(event_bus=bus)
    policies = PolicyManager(event_bus=bus)
    policies.register(TelemetryPolicyAdapter(telemetry))
    policies.register(_FailingPolicy())
    retries = RetryManager(event_bus=bus)
    retries.register(RetryPolicy("local"))
    now = datetime.now(timezone.utc)
    distributed = DistributedCoordinator(Node("node", "local", now, now), event_bus=bus)
    adaptive = AdaptiveRoutingManager(event_bus=bus)
    regions = MultiRegionManager(event_bus=bus)
    regions.register_region(Region("local"))

    telemetry.start()
    telemetry.record(Metric("rc.integration", 1))
    distributed.start()
    adaptive.record_signal(ProviderSignal("local", now))
    assert regions.select_region().selected_region == "local"
    executions = policies.execute(PolicyContext(PolicyStage.BEFORE_REQUEST))
    assert [item.outcome for item in executions] == ["failed", "executed"]
    report = DoctorService(
        policies=policies,
        retries=retries,
        distributed=distributed,
        telemetry=telemetry,
        adaptive=adaptive,
        multiregion=regions,
    ).run()
    assert not report.errors
    expected = {
        "policy.registry",
        "retry.registry",
        "distributed.coordinator",
        "adaptive_routing",
        "multiregion",
    }
    assert expected.issubset({check.name for check in report.checks})

    policies.shutdown()
    telemetry.stop()
    telemetry.stop()
    distributed.stop()
    distributed.stop()
    adaptive.shutdown()
    regions.shutdown()


def test_event_subscriber_failure_and_rc_cli_are_isolated(monkeypatch) -> None:
    bus = EventBus()
    bus.subscribe(lambda _event: (_ for _ in ()).throw(RuntimeError("observer")))
    telemetry = TelemetryManager(event_bus=bus)
    telemetry.start()
    telemetry.record(Metric("still.local", 1))
    assert telemetry.summary()["metrics"] == 1
    service = AICommandService(
        policies=PolicyManager(event_bus=bus),
        retries=RetryManager(event_bus=bus),
        distributed=DistributedCoordinator(
            Node(
                "node", "local", datetime.now(timezone.utc), datetime.now(timezone.utc)
            ),
            event_bus=bus,
        ),
        telemetry=telemetry,
        adaptive=AdaptiveRoutingManager(event_bus=bus),
        multiregion=MultiRegionManager(event_bus=bus),
    )
    monkeypatch.setattr(ai_commands, "_service", service)
    runner = CliRunner()
    for command in (
        "doctor",
        "health",
        "policy",
        "retry",
        "distributed",
        "telemetry",
        "adaptive-routing",
        "multiregion",
    ):
        result = runner.invoke(ai_commands.app, [command, "--help"])
        assert result.exit_code == 0, result.stdout
    assert runner.invoke(ai_commands.app, ["telemetry", "--json"]).exit_code == 0
