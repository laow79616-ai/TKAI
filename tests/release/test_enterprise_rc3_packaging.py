"""Static release checks for the packaged Enterprise reference foundations."""

from __future__ import annotations

import importlib
from pathlib import Path


def test_distribution_configuration_includes_enterprise_reference_packages() -> None:
    """Keep fresh installations able to import the Enterprise foundations."""
    root = Path(__file__).resolve().parents[2]
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    manifest = (root / "MANIFEST.in").read_text(encoding="utf-8")

    assert (
        'include = ["tkai*", "studio*", "enterprise*", "cloud*", "marketplace*"]'
        in pyproject
    )
    assert "include docs/Enterprise.md" in manifest
    assert "include docs/release/enterprise-v3-rc3.md" in manifest
    for module in (
        "enterprise",
        "enterprise.identity",
        "enterprise.organization",
        "enterprise.tenant",
        "enterprise.authorization",
        "enterprise.audit",
        "enterprise.license",
    ):
        assert importlib.import_module(module).__name__ == module


def test_enterprise_rc3_documentation_keeps_the_package_version_single_sourced() -> (
    None
):
    """Enterprise documentation must not invent an independent distribution."""
    root = Path(__file__).resolve().parents[2]
    release = (root / "docs/release/enterprise-v3-rc3.md").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")

    normalized_release = " ".join(release.split())
    assert "Package version: `1.3.0`" in release
    assert "no separate Enterprise package version" in normalized_release
    assert "Enterprise V3.0 reference foundations" in readme
