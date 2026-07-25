"""Offline regression coverage for persistent configuration integration."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from tkai.ai import DoctorService
from tkai.ai.cli_service import AICommandService
from tkai.commands import ai as ai_commands
from tkai.configuration import ConfigurationManager, ConfigurationResolver
from tkai.configuration.sources import (
    EnvironmentConfigurationLoader,
    JSONConfigurationLoader,
    MemoryConfigurationLoader,
    TOMLConfigurationLoader,
    YAMLConfigurationLoader,
)


def test_sources_priority_merge_and_manager(tmp_path: Path) -> None:
    (tmp_path / "user.json").write_text(
        json.dumps({"providers": {"openai": {"timeout": 10}}})
    )
    (tmp_path / ".tkai.yaml").write_text("providers:\n  openai:\n    base_url: local\n")
    (tmp_path / "config.toml").write_text("[application]\nname='tkai'\n")
    resolver = ConfigurationResolver(
        (
            JSONConfigurationLoader(tmp_path / "user.json"),
            TOMLConfigurationLoader(tmp_path / "config.toml"),
            YAMLConfigurationLoader(tmp_path / ".tkai.yaml"),
            EnvironmentConfigurationLoader({"TKAI_PROVIDERS__OPENAI__TIMEOUT": "30"}),
            MemoryConfigurationLoader({"runtime": {"mode": "test"}}),
        )
    )
    manager = ConfigurationManager(resolver)
    config = manager.load()
    assert (
        config.get("providers.openai.timeout") == "30"
        and config.get("providers.openai.base_url") == "local"
    )
    assert manager.has("application.name") and manager.merge(
        {"doctor": {"enabled": True}}
    ).get("doctor.enabled")
    assert manager.credential_defaults("openai")["timeout"] == "30"


def test_doctor_and_cli_configuration_output(monkeypatch) -> None:
    manager = ConfigurationManager(
        ConfigurationResolver(
            (MemoryConfigurationLoader({"application": {"name": "tkai"}}),)
        )
    )
    manager.load()
    report = DoctorService(persistent_configuration=manager).run()
    assert (
        next(
            c for c in report.checks if c.name == "persistent_configuration"
        ).status.value
        == "PASS"
    )
    monkeypatch.setattr(
        ai_commands, "_service", AICommandService(configuration=manager)
    )
    result = CliRunner().invoke(ai_commands.app, ["config", "--json"])
    assert result.exit_code == 0 and json.loads(result.stdout)["source"] == "memory"
