"""Explicit offline identity provider Protocols and a deterministic reference fake."""

from __future__ import annotations

from collections.abc import Mapping
from threading import RLock
from typing import Protocol

from .errors import IdentityNotFoundError
from .models import IdentityDescriptor, IdentityPrincipal


class IdentitySession(Protocol):
    """Reserved session view contract; this foundation creates no sessions."""

    @property
    def session_id(self) -> str: ...

    @property
    def principal(self) -> IdentityPrincipal: ...


class IdentityProvider(Protocol):
    """Explicit provider boundary with no authentication protocol methods."""

    @property
    def descriptor(self) -> IdentityDescriptor: ...

    def resolve(self, principal_id: str) -> IdentityPrincipal: ...
    def capabilities(self) -> frozenset[str]: ...


class ReferenceIdentityProvider:
    """Deterministic, in-memory provider intended only for tests and examples."""

    def __init__(
        self,
        descriptor: IdentityDescriptor,
        principals: Mapping[str, IdentityPrincipal] | None = None,
    ) -> None:
        self._descriptor = descriptor
        self._principals = dict(principals or {})
        self._lock = RLock()

    @property
    def descriptor(self) -> IdentityDescriptor:
        """Return the immutable provider descriptor."""
        return self._descriptor

    def resolve(self, principal_id: str) -> IdentityPrincipal:
        """Resolve an explicit principal id or raise a precise offline error."""
        with self._lock:
            try:
                return self._principals[principal_id]
            except KeyError as exc:
                raise IdentityNotFoundError(
                    f"Reference identity {principal_id!r} was not found."
                ) from exc

    def capabilities(self) -> frozenset[str]:
        """Return declared capabilities without environment or network discovery."""
        return self._descriptor.capabilities
