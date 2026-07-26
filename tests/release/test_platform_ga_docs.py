"""Platform 1.0 documentation release-baseline checks."""

from __future__ import annotations

from pathlib import Path


def test_platform_ga_documentation_declares_consistent_layer_versions() -> None:
    """The Platform release has one documented mapping and no new package version."""
    root = Path(__file__).resolve().parents[2]
    for name in (
        "Platform.md",
        "Architecture.md",
        "Installation.md",
        "DeveloperGuide.md",
        "AdministratorGuide.md",
        "OperationsGuide.md",
        "ReleaseNotes.md",
        "ReleaseChecklist.md",
        "Roadmap.md",
    ):
        assert (root / "docs" / name).is_file()
    platform = (root / "docs" / "Platform.md").read_text(encoding="utf-8")
    assert "Platform | 1.0.0" in platform
    assert "Runtime | 1.3.0" in platform
    assert "SDK | 2.0" in platform
    assert "Studio | 2.1" in platform
    assert "second Python distribution version" in platform


def test_platform_release_docs_link_the_architecture_and_operations_guidance() -> None:
    """The README, changelog, and architecture lead users to Platform guidance."""
    root = Path(__file__).resolve().parents[2]
    readme = (root / "README.md").read_text(encoding="utf-8")
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    architecture = (root / "docs" / "Architecture.md").read_text(encoding="utf-8")
    checklist = (root / "docs" / "ReleaseChecklist.md").read_text(encoding="utf-8")
    assert "TKAI V3.0" in readme and "Platform.md" in readme
    assert "Platform 1.0.0 general-availability preparation" in changelog
    assert "Studio 2.1" in architecture and "SDK 2.0" in architecture
    assert "Node/Vite/typecheck/ESLint" in checklist
