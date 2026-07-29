"""Read-only diagnostic results."""

from ..contracts import DiagnosticResult

DIAGNOSTIC_CATEGORIES = (
    "health",
    "dependency",
    "configuration",
    "validation",
    "recovery",
)

__all__ = ("DIAGNOSTIC_CATEGORIES", "DiagnosticResult")
