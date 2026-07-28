"""Bounded ports used to synchronize risk actions with existing modules."""

from __future__ import annotations

from typing import Protocol


class RiskControlPort(Protocol):
    def apply(self, action: str, reference: str, reason: str) -> None: ...

    def recover(self, reference: str, checkpoint: str) -> bool: ...


class NullRiskControlPort:
    def apply(self, action: str, reference: str, reason: str) -> None:
        return None

    def recover(self, reference: str, checkpoint: str) -> bool:
        return True
