"""CLI and Doctor smoke tests using Typer's local runner only."""

from __future__ import annotations

import json

from typer.testing import CliRunner

import tkai
from tkai.cli import app


def test_root_cli_version_help_and_doctor_are_usable_offline() -> None:
    """Exercise actual entry-point subcommands without requiring configuration."""
    runner = CliRunner()
    help_result = runner.invoke(app, ["--help"])
    version_result = runner.invoke(app, ["version"])
    doctor_result = runner.invoke(app, ["doctor"])

    assert help_result.exit_code == 0
    assert version_result.exit_code == 0
    assert tkai.__version__ in version_result.stdout
    assert doctor_result.exit_code == 0
    assert "Environment check completed" in doctor_result.stdout


def test_ai_doctor_json_output_is_parseable_without_registered_providers() -> None:
    """The read-only Doctor emits JSON and has an understandable empty setup path."""
    result = CliRunner().invoke(app, ["ai", "doctor", "--json"])
    assert result.exit_code == 0
    assert "checks" in json.loads(result.stdout)
