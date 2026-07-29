"""Pipeline extension contracts."""

from __future__ import annotations

from typing import Protocol


class PipelineStage(Protocol):
    """Transforms one local value into another."""

    def process(self, value: object) -> object: ...


__all__ = ("PipelineStage",)
