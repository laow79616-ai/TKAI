"""Read-only TKAI V6 through V11 compatibility adapters."""

from tkai.v12.compatibility_core import (
    SUPPORTED,
    ReadOnlyVersionAdapter,
    compatibility_matrix,
)

__all__ = ("SUPPORTED", "ReadOnlyVersionAdapter", "compatibility_matrix")
