"""Keep the two existing current-version sources synchronized."""

from __future__ import annotations

from pathlib import Path

import tomllib

import tkai


def test_runtime_metadata_readme_and_current_release_report_agree() -> None:
    """Validate current RC-3 markers without rewriting historical RC documents."""
    root = Path(__file__).resolve().parents[2]
    metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    report = (root / "docs/release/v1.2-rc3.md").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")

    assert tkai.__version__ == "1.2.0rc3"
    assert metadata["project"]["version"] == tkai.__version__
    assert tkai.__version__ in readme
    assert "RC-3" in report
