"""Offline regression tests for optional V1.2 Retry Framework behavior."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from tkai.ai import DoctorService, DoctorStatus
from tkai.ai.cli_service import AICommandService
from tkai.commands import ai as ai_commands
from tkai.observability import EventBus
from tkai.policy import PolicyContext, PolicyManager, PolicyStage
from tkai.retry import (
    ExceptionClassification,
    ExponentialBackoffStrategy,
    FixedBackoffStrategy,
    RetryManager,
    RetryPolicy,
    RetryPolicyAdapter,
    RetryPolicyRegistrationError,
    RuntimeRetryAdapter,
    classify_exception,
)


def test_policy_registry_and_exception_classification_are_explicit() -> None:
    """Register policies and classify retryable versus permanent local errors."""
    manager = RetryManager()
    policy = RetryPolicy("transient", max_attempts=3)
    manager.register(policy)
    assert manager.registry.get("transient") is policy
    assert classify_exception(TimeoutError()) is ExceptionClassification.TIMEOUT
    assert classify_exception(ConnectionError()) is ExceptionClassification.TRANSIENT
    assert classify_exception(ValueError()) is ExceptionClassification.PERMANENT
    with pytest.raises(RetryPolicyRegistrationError):
        manager.register(policy)


def test_backoff_budget_decisions_and_observability_are_deterministic() -> None:
    """Retry only retryable errors within the local per-operation budget."""
    bus = EventBus()
    manager = RetryManager(event_bus=bus)
    policy = RetryPolicy(
        "retry", max_attempts=3, backoff=ExponentialBackoffStrategy(0.5, 2, 5)
    )
    attempts = 0
    sleeps: list[float] = []

    def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise TimeoutError("offline")
        return "ok"

    assert manager.run(operation, policy=policy, sleep=sleeps.append) == "ok"
    assert sleeps == [0.5, 1.0]
    assert [event.name for event in bus.events] == ["RetryScheduled", "RetryScheduled"]
    decision = policy.decide(TimeoutError(), 1, policy.budget())
    assert decision.retry
    assert decision.delay_seconds == 0.5


def test_permanent_failure_is_not_retried_and_runtime_adapter_is_opt_in() -> None:
    """Do not retry permanent errors; adapter executes only when caller invokes it."""
    manager = RetryManager()
    adapter = RuntimeRetryAdapter(
        manager, RetryPolicy("single", max_attempts=2, backoff=FixedBackoffStrategy())
    )
    with pytest.raises(ValueError):
        adapter.run(lambda: (_ for _ in ()).throw(ValueError("permanent")))
    assert manager.events[-1].name == "RetryExhausted"


def test_policy_adapter_doctor_and_cli_integrations_are_read_only(monkeypatch) -> None:
    """Expose retry to explicit Policy Engine, Doctor, and CLI without takeover."""
    retries = RetryManager()
    retries.register(RetryPolicy("visible", max_attempts=2))
    policies = PolicyManager()
    policies.register(RetryPolicyAdapter(retries))
    context = PolicyContext(PolicyStage.BEFORE_REQUEST)
    policies.execute(context)
    assert context.data["retry_manager"] is retries

    report = DoctorService(retries=retries).run()
    check = next(item for item in report.checks if item.name == "retry.registry")
    assert check.status is DoctorStatus.PASS
    monkeypatch.setattr(ai_commands, "_service", AICommandService(retries=retries))
    result = CliRunner().invoke(ai_commands.app, ["retry", "--json"])
    assert result.exit_code == 0
    assert '"name": "visible"' in result.stdout
