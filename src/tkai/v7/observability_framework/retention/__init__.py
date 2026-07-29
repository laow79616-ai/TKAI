"""Declarative retention metadata; this framework deletes no source data."""

from collections.abc import Mapping

RetentionMetadata = Mapping[str, object]

__all__ = ("RetentionMetadata",)
