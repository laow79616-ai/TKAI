from __future__ import annotations

import importlib

import pytest

from tkai.v7.security_framework import (
    AuthorizationRequest,
    Effect,
    Permission,
    Policy,
    PolicyRule,
    PolicyType,
    Principal,
    Role,
    SecretReference,
    SecurityFramework,
    SecurityScope,
    SecurityValidationError,
)
from tkai.v7.security_framework.api import (
    SECURITY_ENDPOINTS,
    register_security_framework_routes,
)
from tkai.v7.security_framework.dashboard import SecurityDashboard

SCOPE = SecurityScope("tenant-1", "workspace-1", capability="read", service="catalog")


def framework_with_rbac() -> SecurityFramework:
    framework = SecurityFramework()
    framework.rbac.add_permission(Permission("security.read", "read"))
    framework.rbac.add_permission(Permission("security.admin", "admin"))
    framework.rbac.add_role(Role("viewer", frozenset({"security.read"})))
    framework.rbac.add_role(
        Role("administrator", frozenset({"security.admin"}), frozenset({"viewer"}))
    )
    return framework


def policy(
    policy_id: str,
    effect: Effect = Effect.ALLOW,
    *,
    priority: int = 10,
) -> Policy:
    return Policy(
        policy_id,
        PolicyType.AUTHORIZATION,
        (PolicyRule("security.read", effect, roles=frozenset({"viewer"})),),
        SCOPE,
        priority=priority,
        metadata={"token": "must-not-leak", "owner": "security"},
    )


def request(
    principal: Principal | None = None,
    *,
    scope: SecurityScope = SCOPE,
    capability: str = "read",
    service: str = "catalog",
) -> AuthorizationRequest:
    return AuthorizationRequest(
        principal
        or Principal("alice", frozenset({"viewer"}), "tenant-1", "workspace-1"),
        "security.read",
        scope,
        capability=capability,
        service=service,
    )


def test_required_packages_are_importable() -> None:
    packages = (
        "policies rbac permissions roles principals authorization evaluation "
        "compliance secrets credentials redaction audit integrity validation "
        "configuration isolation events contracts interfaces health metrics "
        "lifecycle dashboard api"
    ).split()
    for package in packages:
        assert importlib.import_module(f"tkai.v7.security_framework.{package}")


def test_policy_registry_validation_priority_and_reference_only_evaluation() -> None:
    framework = framework_with_rbac()
    framework.register_policy(policy("allow-low", priority=1))
    framework.register_policy(policy("deny-high", Effect.DENY, priority=20))
    decision = framework.authorize(request())
    assert not decision.allowed
    assert decision.matched_policy_ids == ("deny-high",)
    assert decision.reference_only
    assert framework.metrics.snapshot()["v7_security_policy_evaluations_total"] == 1


def test_equal_priority_policy_conflict_is_deny_by_default() -> None:
    framework = framework_with_rbac()
    framework.register_policy(policy("allow"))
    conflicting = policy("deny", Effect.DENY)
    assert framework.detect_conflicts(conflicting) == ("allow",)
    framework.register_policy(conflicting)
    decision = framework.authorize(request())
    assert not decision.allowed
    assert set(decision.conflicts) == {"allow", "deny"}


def test_rbac_inheritance_permission_lookup_and_deny_by_default() -> None:
    framework = framework_with_rbac()
    framework.register_policy(policy("allow"))
    admin = Principal("admin", frozenset({"administrator"}), "tenant-1", "workspace-1")
    assert "security.read" in framework.rbac.principal_permissions(admin)
    assert framework.authorize(request(admin)).allowed
    unknown = Principal("unknown", frozenset(), "tenant-1", "workspace-1")
    assert not framework.authorize(request(unknown)).allowed


@pytest.mark.parametrize(
    ("changed", "reason"),
    [
        ({"tenant": "tenant-2"}, "tenant isolation"),
        ({"workspace": "workspace-2"}, "workspace isolation"),
        ({"capability": "write"}, "capability isolation"),
        ({"service": "billing"}, "service isolation"),
    ],
)
def test_tenant_workspace_capability_and_service_isolation(
    changed: dict[str, str], reason: str
) -> None:
    framework = framework_with_rbac()
    framework.register_policy(policy("allow"))
    principal = Principal(
        "alice",
        frozenset({"viewer"}),
        changed.get("tenant", "tenant-1"),
        changed.get("workspace", "workspace-1"),
    )
    decision = framework.authorize(
        request(
            principal,
            capability=changed.get("capability", "read"),
            service=changed.get("service", "catalog"),
        )
    )
    assert not decision.allowed
    assert reason in decision.reason


def test_secrets_are_reference_only_validated_and_redacted() -> None:
    framework = SecurityFramework()
    secret = framework.secrets.register(
        SecretReference(
            "db",
            "environment",
            "env://TKAI_DATABASE_PASSWORD",
            rotation_due_at="2030-01-01T00:00:00+00:00",
            metadata={"owner": "operations"},
        )
    )
    assert secret.reference.startswith("env://")
    assert framework.redact({"password": "plaintext", "nested": {"api_key": "x"}}) == {
        "password": "[REDACTED]",
        "nested": {"api_key": "[REDACTED]"},
    }
    with pytest.raises(ValueError, match="opaque reference"):
        SecretReference("bad", "local", "plaintext")
    with pytest.raises(SecurityValidationError, match="sensitive material"):
        framework.secrets.register(
            SecretReference("bad", "env", "env://SAFE", metadata={"token": "value"})
        )
    assert framework.snapshot()["health"]["plaintext_persistence_enabled"] is False  # type: ignore[index]


def test_compliance_audit_metrics_health_tracing_and_structured_logging() -> None:
    framework = framework_with_rbac()
    traces: list[str] = []
    framework.tracing.register(lambda name, _attributes: traces.append(name))
    framework.register_policy(policy("allow"), actor="operator")
    assert framework.authorize(request()).allowed
    report = framework.compliance()
    snapshot = framework.snapshot()
    assert report.valid
    assert snapshot["health"]["status"] == "healthy"  # type: ignore[index]
    assert snapshot["audit"]
    assert snapshot["metrics"]["v7_security_authorization_total"] == 1  # type: ignore[index]
    assert traces == ["security.authorization.evaluated"]
    assert framework.logs[0]["event"] == "security.policy.registered"
    assert "must-not-leak" not in str(snapshot)


def test_configuration_integrity_and_audit_compliance_are_local() -> None:
    framework = SecurityFramework()
    invalid = framework.validate_configuration({"password": "plaintext"})
    valid = framework.validate_configuration({"password": "env://PASSWORD"})
    integrity = framework.validate_integrity(
        {"policy.json": "sha256:expected"},
        {"policy.json": "sha256:observed"},
    )
    assert not invalid.valid
    assert valid.valid
    assert not integrity.valid
    assert framework.audit_compliance().valid
    assert {event.category for event in framework.history} == {
        "configuration",
        "integrity",
    }


class FakeApp:
    def __init__(self) -> None:
        self.routes: list[tuple[str, tuple[str, ...]]] = []

    def add_api_route(
        self, path: str, _endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        self.routes.append((path, tuple(methods)))


def test_get_only_api_and_dashboard_sections() -> None:
    framework = SecurityFramework()
    app = FakeApp()
    register_security_framework_routes(app, framework)
    assert {path for path, _ in app.routes} == {
        f"/v7/security/{endpoint}" for endpoint in SECURITY_ENDPOINTS
    }
    assert all(methods == ("GET",) for _, methods in app.routes)
    dashboard = SecurityDashboard(framework)
    assert set(dashboard.snapshot()) == set(dashboard.sections)


def test_v6_and_previous_v7_framework_imports_are_unchanged() -> None:
    assert importlib.import_module("tiktok.resource_center")
    for package in (
        "workflow_framework",
        "state_framework",
        "event_fabric",
        "service_mesh",
        "capabilities",
        "resource_framework",
    ):
        assert importlib.import_module(f"tkai.v7.{package}")
