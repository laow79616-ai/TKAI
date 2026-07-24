"""Immutable, serializable Identity Foundation descriptors without credentials."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

IdentityValue = str | int | float | bool | None


def _snapshot(value: Mapping[str, IdentityValue]) -> Mapping[str, IdentityValue]:
    """Return a defensive, read-only mapping snapshot."""
    return MappingProxyType(dict(value))


class IdentityKind(str, Enum):
    """Supported explicit principal categories."""

    ANONYMOUS = "anonymous"
    SYSTEM = "system"
    SERVICE = "service"
    USER = "user"
    BOT = "bot"


@dataclass(frozen=True, slots=True)
class IdentityClaim:
    """A non-secret identity claim used for explicit mapping and description."""

    name: str
    value: IdentityValue
    issuer: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Identity claim name must not be empty.")

    def to_dict(self) -> dict[str, IdentityValue]:
        """Return a JSON-safe claim representation."""
        return {"name": self.name, "value": self.value, "issuer": self.issuer}


@dataclass(frozen=True, slots=True)
class Credential:
    """A credential reference that deliberately excludes a secret or token value."""

    credential_id: str
    kind: str
    fingerprint: str | None = None
    metadata: Mapping[str, IdentityValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.credential_id or not self.kind:
            raise ValueError("Credential id and kind must not be empty.")
        object.__setattr__(self, "metadata", _snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class IdentityAccount:
    """An account reference owned by a principal, without provider-side storage."""

    account_id: str
    principal_id: str
    provider_id: str
    metadata: Mapping[str, IdentityValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.account_id or not self.principal_id or not self.provider_id:
            raise ValueError("Identity account fields must not be empty.")
        object.__setattr__(self, "metadata", _snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class IdentityPrincipal:
    """An immutable identity subject with explicit claims and role references."""

    principal_id: str
    kind: IdentityKind
    display_name: str
    account_id: str | None = None
    claims: tuple[IdentityClaim, ...] = ()
    role_ids: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, IdentityValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.principal_id or not self.display_name:
            raise ValueError(
                "Identity principal id and display name must not be empty."
            )
        object.__setattr__(self, "claims", tuple(self.claims))
        object.__setattr__(self, "role_ids", frozenset(self.role_ids))
        object.__setattr__(self, "metadata", _snapshot(self.metadata))

    @classmethod
    def anonymous(cls) -> IdentityPrincipal:
        """Build the deterministic anonymous identity without ambient context."""
        return cls("anonymous", IdentityKind.ANONYMOUS, "Anonymous")

    @classmethod
    def system(cls, principal_id: str = "system") -> IdentityPrincipal:
        """Build an explicit system identity without an authentication flow."""
        return cls(principal_id, IdentityKind.SYSTEM, "System")

    def to_dict(self) -> dict[str, object]:
        """Return a stable, JSON-safe principal snapshot."""
        return {
            "principal_id": self.principal_id,
            "kind": self.kind.value,
            "display_name": self.display_name,
            "account_id": self.account_id,
            "claims": [claim.to_dict() for claim in self.claims],
            "role_ids": sorted(self.role_ids),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class IdentityContext:
    """Explicit per-operation identity context; it never reads global state."""

    principal: IdentityPrincipal
    request_id: str | None = None
    correlation_id: str | None = None
    metadata: Mapping[str, IdentityValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _snapshot(self.metadata))

    @classmethod
    def anonymous(cls) -> IdentityContext:
        """Build an anonymous context without creating a session or request object."""
        return cls(IdentityPrincipal.anonymous())

    @classmethod
    def system(cls, principal_id: str = "system") -> IdentityContext:
        """Build a system context without environment or ContextVar lookup."""
        return cls(IdentityPrincipal.system(principal_id))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe context snapshot."""
        return {
            "principal": self.principal.to_dict(),
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class IdentityDescriptor:
    """A provider declaration that contains capabilities but no configuration secret."""

    provider_id: str
    principal_kinds: frozenset[IdentityKind]
    capabilities: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, IdentityValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.provider_id:
            raise ValueError("Identity provider id must not be empty.")
        object.__setattr__(self, "principal_kinds", frozenset(self.principal_kinds))
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))
        object.__setattr__(self, "metadata", _snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class RoleMapping:
    """A declarative, non-enforcing mapping from claims to Enterprise role ids."""

    claim_name: str
    accepted_values: frozenset[IdentityValue]
    role_ids: frozenset[str]

    def __post_init__(self) -> None:
        if not self.claim_name:
            raise ValueError("Role mapping claim name must not be empty.")
        object.__setattr__(self, "accepted_values", frozenset(self.accepted_values))
        object.__setattr__(self, "role_ids", frozenset(self.role_ids))

    def applies_to(self, principal: IdentityPrincipal) -> bool:
        """Return whether this declarative mapping matches a principal claim."""
        return any(
            claim.name == self.claim_name and claim.value in self.accepted_values
            for claim in principal.claims
        )


@dataclass(frozen=True, slots=True)
class IdentityGraph:
    """A read-only relationship snapshot for identities, accounts, and roles."""

    principals: Mapping[str, IdentityPrincipal] = field(default_factory=dict)
    relationships: Mapping[str, tuple[str, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "principals", MappingProxyType(dict(self.principals)))
        object.__setattr__(
            self,
            "relationships",
            MappingProxyType(
                {
                    principal_id: tuple(targets)
                    for principal_id, targets in self.relationships.items()
                }
            ),
        )

    def related_to(self, principal_id: str) -> tuple[str, ...]:
        """Return a stable immutable relationship list for a principal."""
        return self.relationships.get(principal_id, ())
