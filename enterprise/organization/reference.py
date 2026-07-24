"""Deterministic reference Organization component for tests and examples only."""

from __future__ import annotations

from .models import OrganizationDescriptor, OrganizationGraph


class ReferenceOrganization:
    """An immutable in-memory organization view with no repository implementation."""

    def __init__(
        self, descriptor: OrganizationDescriptor, graph: OrganizationGraph
    ) -> None:
        self._descriptor = descriptor
        self._graph = graph

    @property
    def descriptor(self) -> OrganizationDescriptor:
        """Return the immutable descriptor supplied by the caller."""
        return self._descriptor

    def snapshot(self) -> OrganizationGraph:
        """Return the immutable graph supplied during explicit construction."""
        return self._graph
