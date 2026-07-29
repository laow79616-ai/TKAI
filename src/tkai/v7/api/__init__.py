"""API contribution contracts; the V6 application remains unchanged."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApiContribution:
    """Metadata for an API surface contributed by a V7 module."""

    module: str
    prefix: str
    contract_version: str = "7.0.0"


__all__ = ("ApiContribution",)
