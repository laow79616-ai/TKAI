"""Protocols for read-only trust mesh consumers."""

from typing import Protocol


class TrustMeshProjection(Protocol):
    def overview(self) -> dict[str, object]: ...

    def health(self) -> dict[str, object]: ...

    def metrics(self) -> dict[str, int]: ...


__all__ = ("TrustMeshProjection",)
