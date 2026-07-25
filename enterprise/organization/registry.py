"""Thread-safe registry for explicitly injected Organization components."""

from __future__ import annotations

from threading import RLock

from .errors import OrganizationConflictError, OrganizationNotFoundError
from .reference import ReferenceOrganization


class OrganizationRegistry:
    """Stores explicit reference organizations; it creates no implicit default."""

    def __init__(self) -> None:
        self._organizations: dict[str, ReferenceOrganization] = {}
        self._lock = RLock()

    def register(self, organization: ReferenceOrganization) -> None:
        """Register an injected reference organization by descriptor id."""
        organization_id = organization.descriptor.organization_id
        with self._lock:
            if organization_id in self._organizations:
                raise OrganizationConflictError(
                    f"Organization {organization_id!r} is already registered."
                )
            self._organizations[organization_id] = organization

    def unregister(self, organization_id: str) -> ReferenceOrganization:
        """Remove and return one organization reference."""
        with self._lock:
            try:
                return self._organizations.pop(organization_id)
            except KeyError as exc:
                raise OrganizationNotFoundError(
                    f"Organization {organization_id!r} was not found."
                ) from exc

    def lookup(self, organization_id: str) -> ReferenceOrganization:
        """Get one registered organization without changing registry state."""
        with self._lock:
            try:
                return self._organizations[organization_id]
            except KeyError as exc:
                raise OrganizationNotFoundError(
                    f"Organization {organization_id!r} was not found."
                ) from exc

    def list(self) -> tuple[ReferenceOrganization, ...]:
        """Return registered organizations in deterministic identifier order."""
        with self._lock:
            return tuple(
                self._organizations[organization_id]
                for organization_id in sorted(self._organizations)
            )
