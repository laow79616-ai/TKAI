"""Storage adapter contracts; no backend is selected by the kernel."""

from __future__ import annotations

from typing import Protocol


class StorageAdapter(Protocol):
    """Explicit persistence boundary."""

    def read(self, key: str) -> bytes | None: ...

    def write(self, key: str, value: bytes) -> None: ...


__all__ = ("StorageAdapter",)
