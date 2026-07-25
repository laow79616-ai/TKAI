"""Offline consistency checks for the committed MIT licensing declaration."""

from __future__ import annotations

from pathlib import Path

from tests.toml_compat import tomllib


def test_mit_license_metadata_and_readme_are_consistent() -> None:
    """Ensure the release license text, package metadata, and README agree."""
    root = Path(__file__).resolve().parents[2]
    license_text = (root / "LICENSE").read_text(encoding="utf-8")
    metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    readme = (root / "README.md").read_text(encoding="utf-8")

    assert license_text.startswith("MIT License\n")
    assert "Permission is hereby granted, free of charge" in license_text
    assert 'THE SOFTWARE IS PROVIDED "AS IS"' in license_text
    assert metadata["project"]["license"] == {"text": "MIT"}
    assert "MIT License" in readme
    assert "(LICENSE)" in readme
