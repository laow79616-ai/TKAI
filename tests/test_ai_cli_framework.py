"""Offline tests for the thin enterprise AI CLI command adapters."""

from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from tkai.ai import (
    AIResponse,
    BaseAIProvider,
    ProviderCapabilities,
    ProviderManager,
    ProviderResponseError,
)
from tkai.ai.cli_service import AICommandService
from tkai.ai.fallback import FallbackCandidate, FallbackPolicy
from tkai.commands import ai as ai_commands
from tkai.observability import (
    EventBus,
    EventDispatcher,
    LoggerAdapter,
    MetricsAdapter,
    RequestStarted,
    TraceAdapter,
)

runner = CliRunner()


class CLIProvider(BaseAIProvider):
    """Offline provider used only to populate manager metadata for CLI tests."""

    name = "primary"
    default_model = "primary-model"
    capabilities = ProviderCapabilities(chat=True, streaming=True, tools=True)

    def generate(
        self, prompt: str, *, model: str | None = None, **options: Any
    ) -> AIResponse:
        return AIResponse(prompt, self.name, model or self.default_model)


def service() -> AICommandService:
    """Create a manager-backed service with no external transport or network use."""
    manager = ProviderManager()
    manager.register(
        CLIProvider(),
        default=True,
        aliases=("main",),
        model_capabilities={
            "vision": ProviderCapabilities(chat=True, vision=True),
        },
    )
    return AICommandService(
        manager,
        fallback=FallbackPolicy(max_attempts=2, retry_budget=1),
        fallback_candidates=(FallbackCandidate("primary", object()),),
    )


def invoke(monkeypatch, args: list[str]):
    """Invoke the command with a fresh isolated service facade."""
    monkeypatch.setattr(ai_commands, "_service", service())
    return runner.invoke(ai_commands.app, args)


def test_doctor_text_and_json(monkeypatch) -> None:
    text = invoke(monkeypatch, ["doctor", "--text"])
    structured = invoke(monkeypatch, ["doctor", "--json"])

    assert text.exit_code == 0
    assert "TKAI AI Doctor" in text.stdout
    assert structured.exit_code == 0
    assert "checks" in json.loads(structured.stdout)


def test_providers_and_capabilities_json(monkeypatch) -> None:
    providers = invoke(monkeypatch, ["providers", "--json"])
    capabilities = invoke(
        monkeypatch,
        ["capabilities", "--provider", "main", "--model", "vision", "--json"],
    )

    assert providers.exit_code == 0
    assert json.loads(providers.stdout)[0]["aliases"] == ["main"]
    assert capabilities.exit_code == 0
    assert json.loads(capabilities.stdout)[0]["override"]


def test_fallback_validate_config_version_and_info(monkeypatch) -> None:
    fallback = invoke(monkeypatch, ["fallback", "--json"])
    validation = invoke(monkeypatch, ["validate-config", "--json"])
    version = invoke(monkeypatch, ["version", "--json"])
    info = invoke(monkeypatch, ["info", "--json"])

    assert fallback.exit_code == 0
    assert json.loads(fallback.stdout)["retry_budget"] == 1
    assert validation.exit_code == 0
    assert "checks" in json.loads(validation.stdout)
    assert version.exit_code == 0
    assert "tkai_version" in json.loads(version.stdout)
    assert info.exit_code == 0
    assert json.loads(info.stdout)["default_provider"] == "primary"


def test_validation_and_configuration_exit_codes(monkeypatch) -> None:
    manager = ProviderManager()
    manager.register(CLIProvider(), default=True)
    manager.default_provider = "missing"
    broken = AICommandService(manager)
    monkeypatch.setattr(ai_commands, "_service", broken)

    validation = runner.invoke(ai_commands.app, ["validate-config"])
    configuration = runner.invoke(
        ai_commands.app, ["capabilities", "--provider", "missing"]
    )

    assert validation.exit_code == 1
    assert configuration.exit_code == 2
    assert "configuration error" in configuration.stderr


def test_runtime_failure_uses_exit_code_three_without_traceback(monkeypatch) -> None:
    configured = service()

    def fail() -> dict[str, object]:
        raise ProviderResponseError("offline runtime failure")

    monkeypatch.setattr(configured, "fallback_summary", fail)
    monkeypatch.setattr(ai_commands, "_service", configured)

    result = runner.invoke(ai_commands.app, ["fallback"])

    assert result.exit_code == 3
    assert "runtime error: ProviderResponseError" in result.stderr
    assert "Traceback" not in result.stdout


def test_help_and_unknown_command_are_safe(monkeypatch) -> None:
    help_result = invoke(monkeypatch, ["--help"])
    unknown_result = invoke(monkeypatch, ["unknown"])

    assert help_result.exit_code == 0
    assert "doctor" in help_result.stdout
    assert unknown_result.exit_code == 2
    assert "Traceback" not in unknown_result.stdout


def test_observability_text_json_and_option_errors_are_safe(monkeypatch) -> None:
    metrics = MetricsAdapter()
    logger = LoggerAdapter()
    trace = TraceAdapter()
    dispatcher = EventDispatcher([metrics, logger, trace])
    bus = EventBus()
    bus.subscribe(dispatcher.dispatch)
    bus.publish(RequestStarted(trace_id="trace-1", correlation_id="request-1"))
    configured = AICommandService(
        observability_bus=bus,
        observability_dispatcher=dispatcher,
        metrics_adapter=metrics,
        logger_adapter=logger,
        trace_adapter=trace,
    )
    monkeypatch.setattr(ai_commands, "_service", configured)

    text = runner.invoke(ai_commands.app, ["observability", "--text"])
    structured = runner.invoke(ai_commands.app, ["observability", "--json"])
    invalid = runner.invoke(ai_commands.app, ["observability", "--unknown"])

    assert text.exit_code == 0
    assert "recent_events" in text.stdout
    assert structured.exit_code == 0
    assert json.loads(structured.stdout)["subscribers"] == 3
    assert invalid.exit_code == 2
