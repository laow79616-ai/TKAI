"""TKAI V3.0 release metadata and artifact contracts."""

from __future__ import annotations

import json
from pathlib import Path

import tkai
from tkai._compat import tomllib

ROOT = Path(__file__).resolve().parents[2]


def test_current_release_versions_are_synchronized() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dashboard = json.loads(
        (ROOT / "dashboard/frontend/package.json").read_text(encoding="utf-8")
    )
    studio = json.loads(
        (ROOT / "studio/frontend/package.json").read_text(encoding="utf-8")
    )
    chart = (ROOT / "deployment/helm/tkai/Chart.yaml").read_text(encoding="utf-8")

    assert project["project"]["version"] == tkai.__version__ == "6.0.0"
    assert dashboard["version"] == studio["version"] == tkai.__version__
    assert "version: 6.0.0" in chart
    assert 'appVersion: "6.0.0"' in chart


def test_v3_release_document_and_packaging_are_complete() -> None:
    document = (ROOT / "docs/release/V3.0.md").read_text(encoding="utf-8")
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    required_sections = {
        "Architecture",
        "Modules",
        "Agent Runtime",
        "Plugin Marketplace",
        "Enterprise Platform",
        "Cloud Native",
        "AI Studio",
        "Enterprise Marketplace",
        "Deployment",
        "Observability",
        "Security",
        "CI/CD",
        "Upgrade Guide",
        "Breaking Changes",
        "Compatibility",
        "Known Limitations",
        "Roadmap",
        "Release Validation",
        "Tag Notes",
    }

    for section in required_sections:
        assert f"## {section}" in document
    assert "include docs/release/V3.0.md" in manifest
