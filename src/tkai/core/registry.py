"""
TKAI Core Registry

Generic object registry.
"""

from __future__ import annotations

from typing import Any, Iterator

from .exceptions import RegistryError


class Registry:
    """Generic registry."""

    def __init__(self) -> None:
        self._items: dict[str, Any] = {}

    def register(self, name: str, obj: Any) -> None:
        """Register an object."""
        if name in self._items:
            raise RegistryError(f"'{name}' already registered")

        self._items[name] = obj

    def unregister(self, name: str) -> Any:
        """Remove an object."""
        if name not in self._items:
            raise RegistryError(f"'{name}' is not registered")

        return self._items.pop(name)

    def get(self, name: str) -> Any:
        """Get an object."""
        if name not in self._items:
            raise RegistryError(f"'{name}' is not registered")

        return self._items[name]

    def has(self, name: str) -> bool:
        """Return whether an object exists."""
        return name in self._items

    def clear(self) -> None:
        """Clear registry."""
        self._items.clear()

    def count(self) -> int:
        """Number of registered objects."""
        return len(self._items)

    def names(self) -> list[str]:
        """Return registered names."""
        return list(self._items.keys())

    def values(self) -> list[Any]:
        """Return registered values."""
        return list(self._items.values())

    def items(self) -> list[tuple[str, Any]]:
        """Return registered items."""
        return list(self._items.items())

    def __contains__(self, name: str) -> bool:
        return self.has(name)

    def __len__(self) -> int:
        return self.count()

    def __iter__(self) -> Iterator[str]:
        return iter(self._items)

    def __getitem__(self, name: str) -> Any:
        return self.get(name)