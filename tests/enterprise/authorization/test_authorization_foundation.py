"""Offline tests for Enterprise Authorization Foundation contracts."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError

import pytest

from enterprise.authorization import (
    ActionDescriptor,
    Attribute,
    AuthorizationContext,
    AuthorizationOutcome,
    AuthorizationRequest,
    Environment,
    PermissionDescriptor,
    ReferenceAuthorizationService,
    ReferencePermissionRegistry,
    ReferenceRoleRegistry,
    Resource,
    ResourceDescriptor,
    RoleDescriptor,
    ScopeDescriptor,
    Subject,
)
from enterprise.authorization.errors import AuthorizationConflictError


def permission() -> PermissionDescriptor:
    """Build a stable RBAC permission descriptor."""
    return PermissionDescriptor(
        "workflow.read",
        ResourceDescriptor("workflow"),
        ActionDescriptor("read"),
        (ScopeDescriptor("tenant", "tenant-1"),),
    )


def request(role_ids: frozenset[str] = frozenset({"viewer"})) -> AuthorizationRequest:
    """Build an explicit reference request with no ambient subject lookup."""
    return AuthorizationRequest(AuthorizationContext("user-1", role_ids), permission())


def test_context_request_and_rbac_descriptors_are_immutable_and_serializable() -> None:
    context = AuthorizationContext("user-1", {"viewer"}, tenant_id="tenant-1")
    descriptor = permission()

    assert context.to_dict()["tenant_id"] == "tenant-1"
    assert descriptor.scopes[0].kind == "tenant"
    with pytest.raises(FrozenInstanceError):
        descriptor.permission_id = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        context.metadata["source"] = "test"  # type: ignore[index]


def test_abac_extension_descriptors_do_not_evaluate_rules() -> None:
    subject = Subject("user-1", (Attribute("department", "engineering"),))
    resource = Resource(ResourceDescriptor("workflow"))
    environment = Environment((Attribute("region", "local"),))

    assert subject.attributes[0].name == "department"
    assert resource.resource.resource_type == "workflow"
    assert environment.attributes[0].value == "local"


def test_reference_service_returns_descriptive_outcomes_without_hooks() -> None:
    role = RoleDescriptor("viewer", "Viewer", {"workflow.read"})
    service = ReferenceAuthorizationService({role.role_id: role})

    assert service.evaluate(request()).outcome is AuthorizationOutcome.ALLOWED
    denied = AuthorizationRequest(
        AuthorizationContext("user-1", {"viewer"}),
        PermissionDescriptor(
            "workflow.write", ResourceDescriptor("workflow"), ActionDescriptor("write")
        ),
    )
    assert service.evaluate(denied).outcome is AuthorizationOutcome.DENIED
    assert service.evaluate(request()).to_dict()["outcome"] == "allowed"
    assert (
        service.evaluate(request(frozenset({"other"}))).outcome
        is AuthorizationOutcome.INDETERMINATE
    )
    assert (
        service.evaluate(request(frozenset())).outcome
        is AuthorizationOutcome.INDETERMINATE
    )
    assert len(service.evaluate_many((request(), request()))) == 2


def test_reference_registries_are_thread_safe_and_return_stable_snapshots() -> None:
    roles = ReferenceRoleRegistry()
    permissions = ReferencePermissionRegistry()

    def register(index: int) -> None:
        role = RoleDescriptor(f"role-{index}", f"Role {index}")
        roles.register(role)
        permissions.register(
            PermissionDescriptor(
                f"permission-{index}",
                ResourceDescriptor("workflow"),
                ActionDescriptor("read"),
            )
        )

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(register, range(8)))

    assert [role.role_id for role in roles.list()] == sorted(
        role.role_id for role in roles.list()
    )
    assert len(permissions.list()) == 8
    with pytest.raises(AuthorizationConflictError):
        roles.register(RoleDescriptor("role-0", "Role 0"))


def test_authorization_documentation_declares_non_enforcement_scope() -> None:
    document = (
        __import__("pathlib").Path(__file__).parents[3] / "docs" / "Authorization.md"
    ).read_text(encoding="utf-8")
    assert "No RBAC enforcement" in document
    assert "No authentication" in document
