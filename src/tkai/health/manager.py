"""Facade for passive health state."""

from __future__ import annotations

from .collector import PassiveHealthCollector
from .registry import HealthRegistry


class HealthManager:
    def __init__(self) -> None:
        self.registry = HealthRegistry()
        self.collector = PassiveHealthCollector(self.registry)
