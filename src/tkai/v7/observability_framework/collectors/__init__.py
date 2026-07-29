"""Collector interface for local reference-based observations."""

from collections.abc import Callable

from ..contracts import DiagnosticResult, ObservationScope

DiagnosticCollector = Callable[[ObservationScope], DiagnosticResult]

__all__ = ("DiagnosticCollector",)
