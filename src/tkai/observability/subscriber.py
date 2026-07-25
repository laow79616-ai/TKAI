"""Subscriber interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import Event


class Subscriber(ABC):
    @abstractmethod
    def supports(self, event: Event) -> bool: ...
    @abstractmethod
    def handle(self, event: Event) -> None: ...
