"""Safe, single-user local deployment support for TKAI."""

from .config import LocalRuntimeConfig
from .manager import LocalRuntimeManager

__all__ = ("LocalRuntimeConfig", "LocalRuntimeManager")
