"""Framework metadata helpers."""

from tkai.v8.contracts import FrameworkKind

SUPPORTED_FRAMEWORKS = tuple(kind.value for kind in FrameworkKind)

__all__ = ("SUPPORTED_FRAMEWORKS",)
