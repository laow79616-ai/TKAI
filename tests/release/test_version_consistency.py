"""Keep the two existing current-version sources synchronized."""

from __future__ import annotations

from pathlib import Path

import tomllib
from typer.testing import CliRunner

import tkai
from tkai.cli import app


def test_runtime_metadata_readme_and_current_release_report_agree() -> None:
    """Validate current RC markers without rewriting historical GA documents."""
    root = Path(__file__).resolve().parents[2]
    metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    report = (root / "docs/release/v1.3-rc2.md").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")

    assert tkai.__version__ == "1.3.0rc1"
    assert metadata["project"]["version"] == tkai.__version__
    assert tkai.__version__ in readme
    assert "Release status" in report


def test_existing_version_command_reports_the_current_candidate() -> None:
    """Keep the established CLI version surface synchronized with package metadata."""
    result = CliRunner().invoke(app, ["version", "show"])

    assert result.exit_code == 0
    assert "TKAI v1.3.0rc1" in result.stdout
