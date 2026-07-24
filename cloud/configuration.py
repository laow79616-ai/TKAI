"""Immutable Cloud configuration descriptors without environment loading."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .models import CloudValue, snapshot


@dataclass(frozen=True, slots=True)
class CloudConfiguration:
    """Explicit configuration for a future Cloud host or gateway adapter."""

    region: str | None = None
    environment: str = "local"
    default_workspace_id: str | None = None
    request_timeout_seconds: float | None = None
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if (
            self.request_timeout_seconds is not None
            and self.request_timeout_seconds < 0
        ):
            raise ValueError("Cloud request timeout must not be negative.")
        object.__setattr__(self, "metadata", snapshot(self.metadata))
