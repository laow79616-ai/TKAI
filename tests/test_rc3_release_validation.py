"""Offline V1.1 RC-3 release artifacts, examples, and version checks."""

from __future__ import annotations

from pathlib import Path

import tomllib

import tkai
from examples.ai import cache, chat, custom_router, multi_provider, plugin


def test_release_version_sources_agree() -> None:
    """Keep package metadata and runtime version from drifting apart."""
    root = Path(__file__).resolve().parents[1]
    metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["project"]["version"] == tkai.__version__


def test_documented_offline_release_examples_run() -> None:
    """Run basic provider, multi-provider, cache, plugin, and routing examples."""
    assert chat.run() == "example:ok"
    assert multi_provider.run() == ("primary:ok", "secondary:ok")
    assert cache.run() == ("cached:ok", 1)
    assert plugin.run() == ["initialize", "BeforeRequest:ok", "shutdown"]
    assert custom_router.run() == "backup"


def test_release_notes_state_compatibility_and_limitations() -> None:
    """Ensure users can discover compatibility, version, and upgrade guidance."""
    root = Path(__file__).resolve().parents[1]
    notes = (root / "docs/release/v1.2-rc1-integration-baseline.md").read_text(
        encoding="utf-8"
    )
    assert "Compatibility" in notes
    assert "Known limitations" in notes
    assert "1.2.0rc1" in notes
