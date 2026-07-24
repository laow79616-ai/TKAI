"""Offline tests for Enterprise Identity Foundation contracts and reference fake."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from enterprise.identity import (
    Credential,
    IdentityClaim,
    IdentityContext,
    IdentityDescriptor,
    IdentityFactory,
    IdentityGraph,
    IdentityKind,
    IdentityPrincipal,
    IdentityRegistry,
    RoleMapping,
)
from enterprise.identity.errors import IdentityConflictError, IdentityNotFoundError


def _descriptor(provider_id: str = "reference") -> IdentityDescriptor:
    return IdentityDescriptor(
        provider_id,
        frozenset({IdentityKind.USER, IdentityKind.SERVICE}),
        frozenset({"resolve", "role_mapping"}),
    )


def _principal() -> IdentityPrincipal:
    return IdentityPrincipal(
        "user-1",
        IdentityKind.USER,
        "Reference User",
        claims=(IdentityClaim("department", "engineering"),),
        role_ids={"developer"},
        metadata={"source": "test"},
    )


def test_principal_context_and_credential_are_immutable_and_serializable() -> None:
    """Reference identity data has no secret value and no mutable state leak."""
    principal = _principal()
    context = IdentityContext(principal, "request-1", "correlation-1")
    credential = Credential("credential-ref", "reference", fingerprint="safe")

    assert context.to_dict()["principal"] == principal.to_dict()
    assert credential.fingerprint == "safe"
    with pytest.raises(FrozenInstanceError):
        principal.display_name = "Changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        principal.metadata["source"] = "other"  # type: ignore[index]


def test_anonymous_and_system_contexts_are_explicit_and_deterministic() -> None:
    """Convenience constructors do not inspect environment or request context."""
    assert IdentityContext.anonymous().principal.kind is IdentityKind.ANONYMOUS
    assert IdentityContext.system("worker").principal.principal_id == "worker"


def test_reference_provider_registry_and_factory_require_explicit_injection() -> None:
    """The registry has no hidden provider and exposes stable capability matches."""
    provider = IdentityFactory.reference_provider(
        _descriptor(), {"user-1": _principal()}
    )
    registry = IdentityRegistry()

    registry.register(provider)

    assert registry.lookup("reference").resolve("user-1") == _principal()
    assert registry.supports("resolve") == (provider,)
    with pytest.raises(IdentityConflictError):
        registry.register(provider)
    assert registry.unregister("reference") is provider
    with pytest.raises(IdentityNotFoundError):
        registry.lookup("reference")


def test_role_mapping_and_graph_are_read_only_and_deterministic() -> None:
    """Role mapping is declarative; graph relationships are immutable snapshots."""
    principal = _principal()
    mapping = RoleMapping("department", {"engineering"}, {"developer"})
    graph = IdentityGraph({principal.principal_id: principal}, {"user-1": ("team-1",)})

    assert mapping.applies_to(principal)
    assert graph.related_to("user-1") == ("team-1",)
    with pytest.raises(TypeError):
        graph.principals["other"] = principal  # type: ignore[index]


def test_reference_provider_never_performs_authentication_or_network_access() -> None:
    """Unknown identities raise an explicit local error without protocol fallback."""
    provider = IdentityFactory.reference_provider(_descriptor())

    with pytest.raises(IdentityNotFoundError, match="missing"):
        provider.resolve("missing")
