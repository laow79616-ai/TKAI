"""Read-only Hyper Intelligence analytics."""

from __future__ import annotations


def coverage(snapshot: dict[str, object]) -> dict[str, int]:
    return {
        name: len(value)
        for name in ("knowledge", "evidence", "signals", "recommendations")
        if isinstance((value := snapshot.get(name)), list)
    }


__all__ = ("coverage",)
