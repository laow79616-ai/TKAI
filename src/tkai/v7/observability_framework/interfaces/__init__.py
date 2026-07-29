"""Public collector protocol."""

from typing import Protocol

from ..contracts import DiagnosticResult, ObservationScope


class DiagnosticCollector(Protocol):
    def __call__(self, scope: ObservationScope) -> DiagnosticResult: ...


__all__ = ("DiagnosticCollector",)
