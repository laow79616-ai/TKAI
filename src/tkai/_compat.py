"""Compatibility imports for supported Python versions."""

from __future__ import annotations

try:
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib  # type: ignore[import-not-found]

__all__ = ["tomllib"]
