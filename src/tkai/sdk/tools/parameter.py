"""Immutable, dependency-free parameter descriptors for local Tool schemas."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ToolParameter:
    """A declared tool argument with a stable primitive annotation name."""

    name: str
    annotation: str = "object"
    required: bool = True
    default: object | None = None
