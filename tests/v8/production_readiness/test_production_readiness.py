from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_v8_release_metadata_is_consistent() -> None:
    release = json.loads((ROOT / "release.json").read_text(encoding="utf-8"))
    frameworks = json.loads(
        (ROOT / "FRAMEWORK_MANIFEST_V8.json").read_text(encoding="utf-8")
    )
    assert release["version"] == "10.0.0"
    assert frameworks["release"] == "8.0.0"
    assert frameworks["framework_count"] == len(frameworks["frameworks"]) == 11
    assert len({item["module"] for item in frameworks["frameworks"]}) == 11


def test_all_v8_framework_routes_are_registered() -> None:
    source = (ROOT / "server/api/app.py").read_text(encoding="utf-8")
    names = (
        "kernel",
        "coordination",
        "intelligence",
        "governance",
        "knowledge",
        "reasoning",
        "decision",
        "planning",
        "simulation",
        "operations",
        "recovery",
    )
    for name in names:
        assert f"register_v8_{name}_routes(app)" in source


def test_required_v8_documentation_and_builder_are_present() -> None:
    for relative in (
        "RELEASE_NOTES_V8.md",
        "docs/v8/Architecture.md",
        "docs/v8/FrameworkOverview.md",
        "docs/v8/Hyper-Kernel-Guide.md",
        "docs/v8/Compatibility-Guide.md",
        "docs/v8/Security-Guide.md",
        "docs/v8/Observability-Guide.md",
        "docs/v8/Production-Operations-Guide.md",
        "docs/v8/Deployment-Guide.md",
        "docs/v8/Windows-Local-Guide.md",
        "docs/v8/Upgrade-V7-to-V8.md",
        "docs/v8/Known-Issues.md",
        "docs/v8/Troubleshooting-Guide.md",
        "scripts/verify-v8-production.py",
    ):
        assert (ROOT / relative).is_file(), relative
