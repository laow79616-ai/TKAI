"""Structured coordination diagnostic contract."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from tkai.v8.hyper_coordination.contracts import immutable_metadata


@dataclass(frozen=True)
class CoordinationDiagnostic:
    code: str
    message: str
    severity: str = "info"
    source: str = "hyper-coordination"
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


__all__ = ("CoordinationDiagnostic",)
