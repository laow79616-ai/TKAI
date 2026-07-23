"""Explicit provider factory with no vendor defaults or environment discovery."""

from __future__ import annotations

from collections.abc import Callable

from .client import ProviderClient
from .configuration import ProviderConfiguration
from .errors import ProviderNotFoundError


class ProviderFactory:
    """Register local builders and construct clients only when callers request one."""

    def __init__(self) -> None:
        self._builders: dict[str, Callable[[ProviderConfiguration], ProviderClient]] = (
            {}
        )

    def register(
        self, name: str, builder: Callable[[ProviderConfiguration], ProviderClient]
    ) -> None:
        """Register one explicit provider builder."""
        if name in self._builders:
            raise ValueError(f"Provider builder already registered: {name}")
        self._builders[name] = builder

    def create(
        self, name: str, configuration: ProviderConfiguration | None = None
    ) -> ProviderClient:
        """Construct one provider through its registered explicit builder."""
        try:
            return self._builders[name](configuration or ProviderConfiguration())
        except KeyError as error:
            raise ProviderNotFoundError(
                f"Provider builder not registered: {name}"
            ) from error
