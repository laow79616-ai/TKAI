from typing import Protocol

from tkai.v8.hyper_decision.contracts import DecisionReference


class DecisionReferenceProvider(Protocol):
    def decision_references(self) -> tuple[DecisionReference, ...]: ...


__all__ = ("DecisionReferenceProvider",)
