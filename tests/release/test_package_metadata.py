"""Minimal offline audit for package metadata and declared entry points."""

from __future__ import annotations

from pathlib import Path

from tests.toml_compat import tomllib


def test_project_metadata_declares_build_runtime_and_cli_contracts() -> None:
    """Validate packaging fields without invoking network-backed build tooling."""
    root = Path(__file__).resolve().parents[2]
    metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]

    assert metadata["build-system"]["build-backend"] == "setuptools.build_meta"
    assert project["name"] == "tkai"
    assert project["requires-python"] == ">=3.10"
    assert project["readme"] == "README.md"
    assert project["scripts"]["tkai"] == "tkai.cli:main"
    assert metadata["tool"]["setuptools"]["package-data"]["tkai"] == [
        "templates/default/README.md",
        "templates/default/template.json",
    ]
    assert {"jinja2", "httpx", "PyYAML", "typer"}.issubset(
        {dependency.split(">=")[0] for dependency in project["dependencies"]}
    )
