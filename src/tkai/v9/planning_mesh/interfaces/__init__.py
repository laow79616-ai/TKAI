from typing import Protocol

from tkai.v9.planning_mesh.contracts import Reference


class PlanningMetadataSource(Protocol):
    def references(self) -> tuple[Reference, ...]: ...


__all__ = ("PlanningMetadataSource",)
