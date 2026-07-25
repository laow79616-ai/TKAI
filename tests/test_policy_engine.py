"""Offline regression coverage for the optional V1.2 Policy Engine."""

from __future__ import annotations

from typer.testing import CliRunner

from tkai.ai import DoctorService, DoctorStatus
from tkai.ai.cli_service import AICommandService
from tkai.commands import ai as ai_commands
from tkai.observability import EventBus
from tkai.policy import (
    BreakerPolicyAdapter,
    CachePolicyAdapter,
    PluginPolicyAdapter,
    PolicyContext,
    PolicyDecision,
    PolicyManager,
    PolicyRegistrationError,
    PolicyStage,
    RateLimitPolicyAdapter,
    RoutingPolicyAdapter,
)


class ExamplePolicy:
    """Small explicit policy used to exercise engine order and isolation."""

    def __init__(
        self,
        name: str,
        calls: list[str],
        *,
        priority: int = 0,
        allowed: bool = True,
        fail: bool = False,
    ) -> None:
        self._name = name
        self.calls = calls
        self._priority = priority
        self._allowed = allowed
        self._fail = fail
        self._enabled = True

    def name(self) -> str:
        return self._name

    def priority(self) -> int:
        return self._priority

    def enabled(self) -> bool:
        return self._enabled

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        self.calls.append(f"evaluate:{self._name}:{context.stage.value}")
        if self._fail:
            raise RuntimeError("isolated")
        return PolicyDecision(self._allowed, "accepted" if self._allowed else "blocked")

    def apply(self, context: PolicyContext) -> None:
        self.calls.append(f"apply:{self._name}")
        context.data[self._name] = True

    def shutdown(self) -> None:
        self.calls.append(f"shutdown:{self._name}")


def test_registry_priority_pipeline_and_disable_are_stable() -> None:
    """Run policies by priority/name and preserve registry-level disable control."""
    calls: list[str] = []
    manager = PolicyManager()
    manager.register(ExamplePolicy("same", calls, priority=1))
    manager.register(ExamplePolicy("high", calls, priority=2))
    manager.register(ExamplePolicy("disabled", calls, priority=3))
    manager.disable("disabled")

    context, results = manager.pipeline.run(PolicyStage.BEFORE_ROUTING)

    assert [result.policy for result in results] == ["disabled", "high", "same"]
    assert [result.outcome for result in results] == ["skipped", "executed", "executed"]
    assert calls == [
        "evaluate:high:before_routing",
        "apply:high",
        "evaluate:same:before_routing",
        "apply:same",
    ]
    assert context.data == {"high": True, "same": True}
    try:
        manager.register(ExamplePolicy("same", calls))
    except PolicyRegistrationError:
        pass
    else:
        raise AssertionError("duplicate policy registration must fail")


def test_failure_isolation_events_and_shutdown() -> None:
    """A failed policy must not prevent later policies or cleanup from running."""
    calls: list[str] = []
    bus = EventBus()
    manager = PolicyManager(event_bus=bus)
    manager.register(ExamplePolicy("failed", calls, priority=2, fail=True))
    manager.register(ExamplePolicy("next", calls, priority=1))

    results = manager.execute(PolicyContext(PolicyStage.AFTER_RESPONSE))
    manager.shutdown()

    assert [result.outcome for result in results] == ["failed", "executed"]
    assert "apply:next" in calls
    assert {event.name for event in bus.events} == {"PolicyFailed", "PolicyExecuted"}
    assert "shutdown:failed" in calls
    assert "shutdown:next" in calls


def test_compatibility_adapters_do_not_modify_existing_policy_objects() -> None:
    """Adapt all V1.1 policy families through the same optional engine contract."""
    adapters = (
        RoutingPolicyAdapter(object()),
        BreakerPolicyAdapter(object()),
        RateLimitPolicyAdapter(object()),
        CachePolicyAdapter(object()),
        PluginPolicyAdapter(object()),
    )
    for adapter in adapters:
        context = PolicyContext(PolicyStage.BEFORE_REQUEST)
        assert adapter.evaluate(context).allowed
        adapter.apply(context)
        assert context.data["policies"][adapter.name()] is adapter.target


def test_doctor_and_cli_report_policy_metadata_without_execution(monkeypatch) -> None:
    """Policy diagnostics and CLI are read-only presentation integrations."""
    manager = PolicyManager()
    manager.register(ExamplePolicy("visible", []))
    report = DoctorService(policies=manager).run()
    check = next(item for item in report.checks if item.name == "policy.registry")
    assert check.status is DoctorStatus.PASS
    assert check.detail["enabled"] == ["visible"]

    monkeypatch.setattr(ai_commands, "_service", AICommandService(policies=manager))
    runner = CliRunner()
    text = runner.invoke(ai_commands.app, ["policy"])
    structured = runner.invoke(ai_commands.app, ["policy", "--json"])
    assert text.exit_code == 0
    assert "visible" in text.stdout
    assert structured.exit_code == 0
    assert '"name": "visible"' in structured.stdout
