"""Explicit factory for deterministic, non-persistent reference organizations."""

from __future__ import annotations

from .models import OrganizationDescriptor, OrganizationGraph
from .reference import ReferenceOrganization


class OrganizationFactory:
    """Creates only caller-requested reference organization components."""

    @staticmethod
    def reference(
        descriptor: OrganizationDescriptor, graph: OrganizationGraph
    ) -> ReferenceOrganization:
        """Build an offline reference organization without a repository or network."""
        return ReferenceOrganization(descriptor, graph)
