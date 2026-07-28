"""Risk extension interfaces for host implementations."""

from typing import Protocol


class RiskEvaluator(Protocol):
    def evaluate(self, resource: str) -> str: ...


__all__ = ("RiskEvaluator",)
