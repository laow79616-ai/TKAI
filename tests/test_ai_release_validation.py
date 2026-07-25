"""Offline V1.0 RC compatibility, example, and documentation validation."""

from __future__ import annotations

import inspect
from pathlib import Path

from typer.testing import CliRunner

from examples.ai import (
    async_chat,
    capability,
    chat,
    cli,
    doctor,
    fallback,
    multi_provider,
    streaming,
)
from tkai.ai import (
    AIClient,
    AIProvider,
    OpenAICompatibleProvider,
    ProviderManager,
)
from tkai.commands.ai import app as ai_app


def test_public_ai_compatibility_surface_is_stable() -> None:
    """Audit legacy and additive public methods without issuing provider calls."""
    assert callable(AIClient.generate)
    assert callable(AIProvider.generate)
    assert callable(ProviderManager.register)
    assert callable(ProviderManager.get)
    assert callable(ProviderManager.chat)
    assert callable(ProviderManager.embed)
    assert callable(ProviderManager.close)
    assert callable(ProviderManager.achat)
    assert callable(ProviderManager.astream_chat)
    assert callable(OpenAICompatibleProvider.chat)
    assert callable(OpenAICompatibleProvider.stream_chat)
    assert callable(OpenAICompatibleProvider.close)
    assert callable(OpenAICompatibleProvider.achat)
    assert callable(OpenAICompatibleProvider.astream_chat)
    assert callable(OpenAICompatibleProvider.aclose)
    assert "provider" in inspect.signature(ProviderManager.chat).parameters


def test_legacy_ai_cli_commands_remain_registered() -> None:
    """Keep prior command names available without executing provider work."""
    runner = CliRunner()
    for command in ("list", "models", "chat", "embed"):
        result = runner.invoke(ai_app, [command, "--help"])
        assert result.exit_code == 0


def test_all_documented_ai_examples_run_offline() -> None:
    """Execute every AI example using only deterministic local fakes."""
    assert chat.run() == "example:ok"
    assert async_chat.run() == "example:ok"
    assert streaming.run() == ["example:ok"]
    assert multi_provider.run() == ("primary:ok", "secondary:ok")
    assert capability.run() == "example:ok"
    assert fallback.run() == "backup"
    assert "checks" in doctor.run()
    assert "tkai_version" in cli.run()


def test_release_documentation_and_version_metadata_are_present() -> None:
    """Verify release documents cover the V1.0 RC public handoff."""
    root = Path(__file__).resolve().parents[1]
    required = {
        "README.md": "1.2.0",
        "docs/Architecture.md": "AI providers",
        "docs/Migration.md": "Async migration",
        "docs/Providers.md": "Provider Development Guide",
        "docs/CLI.md": "Exit codes",
        "docs/Doctor.md": "DoctorService",
        "docs/Release.md": "V1.0 Release Checklist",
        "CHANGELOG.md": "V1.0 RC",
    }
    for relative_path, marker in required.items():
        assert marker in (root / relative_path).read_text(encoding="utf-8")
