"""Release-document regression checks for the V1.3 RC-3 packaging gate."""

from __future__ import annotations

from pathlib import Path


def test_v13_rc3_documentation_records_the_candidate_and_artifact_validation() -> None:
    """Keep the release handoff aligned with the audited package candidate."""
    root = Path(__file__).resolve().parents[2]
    report = (root / "docs/release/v1.3-rc3.md").read_text(encoding="utf-8")
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")

    assert "1.3.0rc1" in report
    assert "wheel" in report.lower()
    assert "sdist" in report.lower()
    assert "V1.3 RC-3" in changelog
