"""Workflow framework health projections."""

from ..framework import WorkflowFramework


def health(framework: WorkflowFramework) -> object:
    return framework.snapshot()["health"]


__all__ = ("health",)
