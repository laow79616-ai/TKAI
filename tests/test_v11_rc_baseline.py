"""Offline RC-1 public-surface and compatibility regression checks."""

from __future__ import annotations

import importlib
import json
import pkgutil
from datetime import datetime, timezone
from pathlib import Path

from typer.testing import CliRunner

import tkai
from tkai import (
    cache,
    circuit_breaker,
    configuration,
    credentials,
    health,
    load,
    observability,
    plugins,
    rate_limit,
    routing,
)
from tkai.ai import AIClient, DoctorService, ProviderManager
from tkai.cache import CacheEntry
from tkai.circuit_breaker import CircuitBreakerSnapshot, CircuitState
from tkai.commands.ai import app as ai_app
from tkai.configuration import Configuration
from tkai.credentials import Credential
from tkai.health import HealthSnapshot, HealthStatus
from tkai.load import LoadStatus, ProviderLoadSnapshot
from tkai.observability import Event
from tkai.plugins import PluginManager, PluginMetadata
from tkai.rate_limit import RateLimitSnapshot
from tkai.routing import RoutingDecision


def test_rc_public_facades_and_legacy_imports_are_available() -> None:
    """Keep documented public and historical imports independent of order."""
    assert tkai.__version__ == "1.0.0rc1"
    assert callable(AIClient.generate)
    assert callable(ProviderManager.chat)
    assert callable(DoctorService.run)
    assert credentials.Credential is Credential
    assert configuration.Configuration is Configuration
    assert health.HealthSnapshot is HealthSnapshot
    assert observability.Event is Event
    assert circuit_breaker.CircuitState is CircuitState
    assert routing.RoutingDecision is RoutingDecision
    assert load.ProviderLoadSnapshot is ProviderLoadSnapshot
    assert rate_limit.RateLimitSnapshot is RateLimitSnapshot
    assert cache.CacheEntry is CacheEntry
    assert plugins.PluginManager is PluginManager

    from tkai.config import ConfigManager
    from tkai.plugins import Plugin
    from tkai.template_engine import TemplateManager
    from tkai.templates.manager import TemplateManager as LegacyTemplateManager

    assert ConfigManager is not None
    assert Plugin is not None
    assert TemplateManager is LegacyTemplateManager


def test_additive_services_are_not_enabled_by_default() -> None:
    """Protect V1 provider execution from accidental optional-service takeover."""
    manager = ProviderManager()
    assert manager.names() == []
    assert PluginManager().names() == []
    assert routing.RoutingManager().list() == []
    assert load.LoadManager().list() == []
    assert rate_limit.RateLimitManager().list() == []
    assert health.HealthManager().registry.list() == []
    assert circuit_breaker.CircuitBreakerManager().list() == []


def test_public_models_have_safe_json_stable_representations() -> None:
    """Exercise immutable diagnostic models without exposing credentials."""
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    credential = Credential("openai", "secret-value", source="memory")
    assert "secret-value" not in repr(credential)
    assert credential.masked() == "se***ue"

    values = (
        CircuitBreakerSnapshot("one", CircuitState.OPEN, opened_at=now).to_dict(),
        RoutingDecision(
            "one",
            ("one",),
            "selected",
            0.0,
            0,
            1,
            HealthStatus.HEALTHY,
            CircuitState.CLOSED,
            now,
        ).to_dict(),
        ProviderLoadSnapshot("one", status=LoadStatus.LOW, last_updated=now).to_dict(),
        RateLimitSnapshot("one", reset_at=now, last_updated=now).to_dict(),
        CacheEntry("key", {"value": 1}, created_at=now).to_dict(),
        PluginMetadata("one", "1.0", capabilities=frozenset({"hook"})).to_dict(),
    )
    for value in values:
        json.dumps(value, sort_keys=True)

    assert (
        Configuration({"provider": {"timeout": 30}}, "memory").get("provider.timeout")
        == 30
    )
    assert HealthSnapshot("one").status is HealthStatus.UNKNOWN
    event = Event("RequestStarted", now, correlation_id="rc-1")
    assert event.correlation_id == "rc-1"


def test_legacy_plugin_lifecycle_and_rc_ai_commands_remain_registered() -> None:
    """Keep activate/deactivate protocol and all RC CLI command names present."""
    assert hasattr(plugins.Plugin, "activate")
    assert hasattr(plugins.Plugin, "deactivate")
    runner = CliRunner()
    commands = (
        "doctor",
        "health",
        "observability",
        "breaker",
        "routing",
        "load",
        "rate-limit",
        "cache",
        "plugins",
        "list",
        "models",
        "chat",
        "embed",
    )
    for command in commands:
        result = runner.invoke(ai_app, [command, "--help"])
        assert result.exit_code == 0, result.stdout


def test_doctor_aggregates_optional_subsystem_checks_without_mutation() -> None:
    """A missing optional service is diagnostic information, never a crash."""
    report = DoctorService().run()
    names = {check.name for check in report.checks}
    assert {
        "credentials",
        "persistent_configuration",
        "health",
        "observability.event_bus",
        "circuit_breaker",
        "routing",
        "load",
        "rate_limit",
        "cache",
        "plugins",
    }.issubset(names)
    assert report.errors == 0
    assert json.loads(report.to_json()) == report.to_dict()


def test_rc_release_documents_record_api_contract_and_limitations() -> None:
    """Keep the public inventory and release gate visible to maintainers."""
    root = Path(__file__).resolve().parents[1]
    api = (root / "docs/release/v1.1-public-api.md").read_text(encoding="utf-8")
    checklist = (root / "docs/release/v1.1-rc1-checklist.md").read_text(
        encoding="utf-8"
    )
    assert "Plugins" in api
    assert "Explicit opt-in policy" in api
    assert "No OpenTelemetry or Prometheus exporter" in checklist
    assert "1.0.0rc1" in checklist


def test_all_tkai_modules_import_without_explicit_provider_or_plugin_startup() -> None:
    """Smoke-test package imports for cycles and import-time side effects."""
    modules = sorted(
        item.name for item in pkgutil.walk_packages(tkai.__path__, f"{tkai.__name__}.")
    )
    for module_name in modules:
        importlib.import_module(module_name)
