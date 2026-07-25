"""Static Cloud RC-3 packaging and release-documentation regression checks."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_cloud_rc3_documentation_and_manifest_are_release_ready() -> None:
    """Cloud release docs are shipped explicitly with the source distribution."""
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    for relative_path in (
        "docs/Cloud.md",
        "docs/release/cloud-v4-rc1.md",
        "docs/release/cloud-v4-rc2.md",
        "docs/release/cloud-v4-rc3.md",
    ):
        assert f"include {relative_path}" in manifest
        assert (ROOT / relative_path).is_file()


def test_cloud_foundations_are_discovered_as_package_content() -> None:
    """Project package discovery continues to include the additive Cloud layer."""
    configuration = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert (
        'include = ["tkai*", "studio*", "enterprise*", "cloud*", '
        '"marketplace*", "server*"]'
    ) in configuration
    for package in (
        "workspace",
        "project",
        "deployment",
        "storage",
        "execution",
        "gateway",
    ):
        assert (ROOT / "cloud" / package / "__init__.py").is_file()


def test_cloud_release_document_records_metadata_and_offline_scope() -> None:
    """The release report states the shared package version and offline limits."""
    document = (ROOT / "docs/release/cloud-v4-rc3.md").read_text(encoding="utf-8")
    assert "1.3.0" in document
    assert "without network access" in document
    assert "reference" in document.lower()
