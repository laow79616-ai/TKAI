"""Regression checks for the TKAI 2.0 RC-3 release handoff."""

from __future__ import annotations

from pathlib import Path

import tkai
from tkai._compat import tomllib


def test_tkai_2_rc3_report_records_packaging_validation_and_version_source() -> None:
    """Keep the SDK release document aligned with package metadata."""
    root = Path(__file__).resolve().parents[2]
    report = (root / "docs/release/tkai-2.0-rc3.md").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    installed_metadata = (root / "src/tkai.egg-info/PKG-INFO").read_text(
        encoding="utf-8"
    )
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]

    assert project["version"] == tkai.__version__ == "1.3.0"
    assert "Version: 1.3.0" in installed_metadata
    assert "wheel" in report.lower()
    assert "sdist" in report.lower()
    assert "fresh-install" in report.lower()
    assert "TKAI 2.0 RC-3" in changelog
    assert "TKAI 2.0 RC-3 release validation" in readme
