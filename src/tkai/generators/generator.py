"""
TKAI Generator Manager

Generator registry and dispatcher.
"""

from __future__ import annotations

from typing import Any, Iterator

from tkai.core.context import Context
from tkai.core.exceptions import GeneratorError

from .base import BaseGenerator


class GeneratorManager:
    """Generator manager."""

    def __init__(self, context: Context) -> None:
        self.context = context
        self._generators: dict[str, BaseGenerator] = {}

    def register(
        self,
        generator: BaseGenerator,
        *,
        overwrite: bool = False,
    ) -> None:
        """
        Register a generator.
        """
        generator_name = generator.name

        if generator_name in self._generators and not overwrite:
            raise GeneratorError(
                f"Generator '{generator_name}' already registered."
            )

        self._generators[generator_name] = generator

    def unregister(self, generator_name: str) -> BaseGenerator:
        """
        Remove a generator.
        """
        if generator_name not in self._generators:
            raise GeneratorError(
                f"Generator '{generator_name}' not found."
            )

        return self._generators.pop(generator_name)

    def get(self, generator_name: str) -> BaseGenerator:
        """
        Get a registered generator.
        """
        if generator_name not in self._generators:
            raise GeneratorError(
                f"Generator '{generator_name}' not found."
            )

        return self._generators[generator_name]

    def has(self, generator_name: str) -> bool:
        """
        Check whether generator exists.
        """
        return generator_name in self._generators

    def clear(self) -> None:
        """
        Remove all generators.
        """
        self._generators.clear()

    def count(self) -> int:
        """
        Number of registered generators.
        """
        return len(self._generators)

    def list(self) -> list[str]:
        """
        Return generator names.
        """
        return sorted(self._generators.keys())

    def values(self) -> list[BaseGenerator]:
        """
        Return generator instances.
        """
        return list(self._generators.values())

    def items(self) -> list[tuple[str, BaseGenerator]]:
        """
        Return registry items.
        """
        return list(self._generators.items())

    def generate(
        self,
        generator_name: str,
        **kwargs: Any,
    ) -> Any:
        """
        Execute a generator.
        """
        generator = self.get(generator_name)
        return generator.generate(**kwargs)

    def __contains__(self, generator_name: str) -> bool:
        return self.has(generator_name)

    def __len__(self) -> int:
        return self.count()

    def __iter__(self) -> Iterator[BaseGenerator]:
        return iter(self._generators.values())