"""Immutable Project descriptors without deployment, storage, or secret data."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..models import CloudValue, snapshot


@dataclass(frozen=True, slots=True)
class ProjectDescriptor:
    """Declares optional project capabilities without enabling them."""

    project_id: str
    capabilities: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.project_id:
            raise ValueError("Project descriptor requires a project id.")
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))
        object.__setattr__(self, "metadata", snapshot(self.metadata))
