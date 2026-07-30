"""Read-only interfaces for reasoning metadata providers."""

from typing import Protocol

from tkai.v8.hyper_reasoning.contracts import ReasoningReference


class ReasoningMetadataProvider(Protocol):
    def discover(self) -> tuple[ReasoningReference, ...]: ...


__all__ = ("ReasoningMetadataProvider",)
