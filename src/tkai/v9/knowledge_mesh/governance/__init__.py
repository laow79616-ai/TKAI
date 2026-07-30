"""Non-authorizing governance metadata."""

from __future__ import annotations


def authorizes_execution(_value: object) -> bool:
    return False


__all__ = ("authorizes_execution",)
