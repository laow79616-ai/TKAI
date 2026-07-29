"""In-memory state contracts; durable backends belong in storage adapters."""

from __future__ import annotations

from typing import Protocol


class StateStore(Protocol):
    """Minimal state store contract."""

    def get(self, key: str) -> object | None: ...

    def set(self, key: str, value: object) -> None: ...


__all__ = ("StateStore",)
