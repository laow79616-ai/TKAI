"""Static RC-3 packaging checks for the independently packaged Studio layer."""

from __future__ import annotations

from pathlib import Path


def test_distribution_configuration_includes_studio_and_frontend_sources() -> None:
    """Studio backend and frontend source assets remain discoverable by setuptools."""
    root = Path(__file__).resolve().parents[2]
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert 'where = ["src", "."]' in pyproject
    assert (
        'include = ["tkai*", "studio*", "enterprise*", "cloud*", '
        '"marketplace*", "server*"]'
    ) in pyproject
    assert 'studio = ["frontend/**", "assets/**", "docs/**"]' in pyproject
    for path in (
        root / "studio" / "__init__.py",
        root / "studio" / "backend" / "app.py",
        root / "studio" / "frontend" / "src" / "api.ts",
        root / "studio" / "frontend" / "src" / "main.tsx",
    ):
        assert path.is_file()


def test_studio_rc3_documentation_keeps_the_package_version_single_sourced() -> None:
    """Release docs name the package version without inventing a Studio one."""
    root = Path(__file__).resolve().parents[2]
    release = (root / "docs" / "release" / "studio-v2.1-rc3.md").read_text(
        encoding="utf-8"
    )
    assert "Package version: `1.3.0`" in release
    assert "no separate package version" in release
    assert "Node/npm dependencies" in release
    assert "are not installed in this environment" in release
