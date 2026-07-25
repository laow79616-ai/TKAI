"""Stable public-module imports must remain offline and side-effect free."""

from __future__ import annotations

import importlib

import pytest


@pytest.mark.parametrize(
    "module",
    (
        "tkai",
        "tkai.core",
        "tkai.config",
        "tkai.commands",
        "tkai.generators",
        "tkai.template_engine",
        "tkai.policy",
        "tkai.retry",
        "tkai.observability",
        "tkai.telemetry",
        "tkai.distributed",
        "tkai.adaptive",
        "tkai.multiregion",
        "tkai.ai.runtime",
    ),
)
def test_public_module_imports_succeed(module: str) -> None:
    """Import supported module surfaces without provider initialization."""
    assert importlib.import_module(module).__name__ == module
