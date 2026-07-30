from typing import Protocol

from tkai.v9.decision_mesh.contracts import Reference


class ReferenceProvider(Protocol):
    def references(self) -> tuple[Reference, ...]: ...


__all__ = ("ReferenceProvider",)
