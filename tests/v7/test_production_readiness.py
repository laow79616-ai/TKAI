from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_release_and_framework_manifests_are_consistent() -> None:
    release = json.loads((ROOT / "release.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    frameworks = json.loads(
        (ROOT / "FRAMEWORK_MANIFEST.json").read_text(encoding="utf-8")
    )
    integrity = json.loads(
        (ROOT / "INTEGRITY_MANIFEST.json").read_text(encoding="utf-8")
    )

    assert release["version"] == manifest["version"] == frameworks["release"]
    assert release["version"] == "7.0.0"
    assert len(frameworks["frameworks"]) == 15
    assert len({item["name"] for item in frameworks["frameworks"]}) == 15
    assert integrity["algorithm"] == "SHA-256"


def test_release_packaging_includes_v7_evidence() -> None:
    build = (ROOT / "scripts/build-release.ps1").read_text(encoding="utf-8")
    validate = (ROOT / "scripts/validate-release.ps1").read_text(encoding="utf-8")
    for name in (
        "RELEASE_NOTES_V7.md",
        "FRAMEWORK_MANIFEST.json",
        "INTEGRITY_MANIFEST.json",
    ):
        assert name.lower() in build.lower()
        if name != "RELEASE_NOTES_V7.md":
            assert name.lower() in validate.lower()


def test_v7_release_documentation_is_present() -> None:
    for relative in (
        "RELEASE_NOTES_V7.md",
        "docs/v7/Architecture.md",
        "docs/v7/FrameworkOverview.md",
        "docs/v7/OperationsGuide.md",
        "docs/v7/WindowsGuide.md",
        "docs/v7/ProductionReadinessReport.md",
        "docs/ProductionDeployment.md",
        "docs/Upgrade.md",
        "docs/KnownIssues.md",
    ):
        assert (ROOT / relative).is_file(), relative
