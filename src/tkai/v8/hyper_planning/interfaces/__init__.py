from typing import Protocol

from tkai.v8.hyper_planning.contracts import PlanningReference


class PlanningMetadataProvider(Protocol):
    def planning_references(self) -> tuple[PlanningReference, ...]: ...


__all__ = ("PlanningMetadataProvider",)
