"""Offline credential discovery, diagnostics, and CLI tests."""

from __future__ import annotations

from typer.testing import CliRunner

from tkai.ai import DoctorService
from tkai.ai.cli_service import AICommandService
from tkai.commands import ai as ai_commands
from tkai.credentials import Credential, CredentialManager, CredentialResolver
from tkai.credentials.sources import (
    DotenvCredentialProvider,
    EnvironmentCredentialProvider,
    RuntimeCredentialProvider,
    StaticCredentialProvider,
)


def credential(provider: str, key: str) -> Credential:
    """Create a local test credential without any provider interaction."""
    return Credential(provider, key)


def test_sources_resolution_priority_manager_and_masking() -> None:
    runtime = RuntimeCredentialProvider({"openai": credential("openai", "runtime-key")})
    environment = EnvironmentCredentialProvider({"OPENAI_API_KEY": "environment-key"})
    dotenv = DotenvCredentialProvider(
        text="OPENAI_API_KEY=dotenv-key\nGOOGLE_API_KEY=google"
    )
    static = StaticCredentialProvider({"openai": credential("openai", "static-key")})
    manager = CredentialManager(
        CredentialResolver((runtime, environment, dotenv, static))
    )

    assert manager.get("openai").source == "runtime"
    assert manager.get("openai").api_key == "runtime-key"
    assert manager.get("gemini").source == "dotenv"
    assert manager.has("openai")
    assert manager.mask("openai") == "ru***ey"
    assert "runtime-key" not in repr(manager.get("openai"))
    manager.reload()


def test_doctor_and_cli_report_safe_credential_metadata(monkeypatch) -> None:
    manager = CredentialManager(
        CredentialResolver(
            (StaticCredentialProvider({"openai": credential("openai", "secret-key")}),)
        )
    )
    report = DoctorService(credentials=manager).run()
    check = next(item for item in report.checks if item.name == "credentials.openai")
    assert check.status.value == "PASS"
    assert "secret-key" not in report.to_json()

    service = AICommandService(credentials=manager)
    monkeypatch.setattr(ai_commands, "_service", service)
    result = CliRunner().invoke(ai_commands.app, ["credentials", "--json"])
    assert result.exit_code == 0
    assert "secret-key" not in result.stdout
    assert '"source": "static"' in result.stdout
