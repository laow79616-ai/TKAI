"""Metadata validation and safe projection."""

from __future__ import annotations

from collections.abc import Mapping

from tkai.v7.security import filter_secrets


def safe_metadata(metadata: Mapping[str, object]) -> dict[str, object]:
    return filter_secrets(metadata)


__all__ = ("safe_metadata",)
