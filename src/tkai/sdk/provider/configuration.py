"""Immutable provider settings with no environment or secret discovery."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from .errors import ProviderConfigurationError


@dataclass(frozen=True, slots=True)
class ProviderConfiguration:
    """Caller-supplied provider configuration, safe to share across adapters."""

    timeout_seconds: float = 30.0
    retry_attempts: int = 0
    headers: Mapping[str, str] = field(default_factory=dict)
    base_url: str | None = None
    model: str | None = None
    api_version: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0 or self.retry_attempts < 0:
            raise ProviderConfigurationError(
                "Provider timeout must be positive and retry attempts non-negative."
            )
        object.__setattr__(self, "headers", MappingProxyType(dict(self.headers)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
