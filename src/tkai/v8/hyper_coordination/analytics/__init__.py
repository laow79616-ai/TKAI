"""Read-only coordination analytics helpers."""

from __future__ import annotations


def graph_statistics(snapshot: dict[str, object]) -> dict[str, int]:
    """Count graph nodes and outgoing references."""

    nodes = sum(len(value) for value in snapshot.values() if isinstance(value, dict))
    edges = sum(
        len(targets)
        for value in snapshot.values()
        if isinstance(value, dict)
        for targets in value.values()
        if isinstance(targets, (list, tuple))
    )
    return {"nodes": nodes, "edges": edges}


__all__ = ("graph_statistics",)
