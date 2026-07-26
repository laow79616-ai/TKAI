from __future__ import annotations

from datetime import timedelta

import pytest

from security_platform import (
    METRICS,
    AuthenticationRequest,
    AuthenticationResult,
    ComplianceMapping,
    Delegation,
    Identity,
    IdentityKind,
    IncidentSeverity,
    KeyReference,
    RoleBinding,
    RotationPolicy,
    SecretReference,
    SecurityPlatform,
    SecurityScope,
    TokenKind,
)


class PasswordAdapter:
    def authenticate(self, request: AuthenticationRequest) -> AuthenticationResult:
        return AuthenticationResult(
            request.credential == "correct",
            request.identity_id,
            request.method,
            None if request.credential == "correct" else "invalid credentials",
        )


class RotationAdapter:
    def rotate(self, reference: SecretReference) -> SecretReference:
        return SecretReference(
            reference.name, reference.provider, reference.path, "version-2"
        )


def configured() -> tuple[SecurityPlatform, SecurityScope]:
    platform = SecurityPlatform(session_limit=1, brute_force_limit=2)
    scope = SecurityScope("tenant-a", "workspace-a", "alice")
    platform.create_identity(
        Identity(
            "alice",
            IdentityKind.USER,
            scope.tenant,
            scope.workspace,
            "Alice",
        ),
        scope,
    )
    return platform, scope


def test_identity_types_and_scope_isolation() -> None:
    platform, scope = configured()
    for kind in IdentityKind:
        if kind is IdentityKind.USER:
            continue
        platform.create_identity(
            Identity(
                kind.value,
                kind,
                scope.tenant,
                scope.workspace,
                kind.value,
            ),
            scope,
        )
    assert {item.kind for item in platform.list_identities(scope)} == set(IdentityKind)
    with pytest.raises(PermissionError):
        platform.create_identity(
            Identity(
                "other",
                IdentityKind.USER,
                "tenant-b",
                scope.workspace,
                "Other",
            ),
            scope,
        )


def test_authentication_api_keys_service_tokens_and_brute_force() -> None:
    platform, scope = configured()
    platform.bind_authenticator("password", PasswordAdapter())
    good = AuthenticationRequest(
        "password", "alice", "correct", scope.tenant, scope.workspace
    )
    assert platform.authenticate(good).authenticated
    platform.register_api_key("alice", "api-secret")
    platform.register_service_token("alice", "service-secret")
    for method, credential in (
        ("api_key", "api-secret"),
        ("service_token", "service-secret"),
    ):
        assert platform.authenticate(
            AuthenticationRequest(
                method, "alice", credential, scope.tenant, scope.workspace
            )
        ).authenticated
    bad = AuthenticationRequest(
        "password", "alice", "wrong", scope.tenant, scope.workspace
    )
    assert not platform.authenticate(bad).authenticated
    assert not platform.authenticate(bad).authenticated
    assert not platform.authenticate(good).authenticated
    assert platform.metrics.snapshot()["auth_failures_total"] == 3
    assert any(item.category == "brute_force" for item in platform.threats)


def test_rbac_abac_delegation_tokens_sessions_and_least_privilege() -> None:
    platform, scope = configured()
    platform.set_role("reader", {"security:read", "incident:read"})
    platform.bind_role(
        RoleBinding("alice", "reader", scope.tenant, scope.workspace), scope
    )
    assert platform.authorize("alice", "security:read", "dashboard", scope).allowed
    assert not platform.authorize("alice", "security:write", "dashboard", scope).allowed
    platform.create_identity(
        Identity(
            "agent-a",
            IdentityKind.AGENT,
            scope.tenant,
            scope.workspace,
            "Agent",
        ),
        scope,
    )
    platform.delegate(
        Delegation(
            "delegation-a",
            "alice",
            "agent-a",
            frozenset({"incident:read"}),
            platform.audit_events[-1].occurred_at + timedelta(hours=1),
        ),
        scope,
    )
    assert "incident:read" in platform.permissions_for("agent-a", scope)
    with pytest.raises(PermissionError):
        platform.issue_token(
            TokenKind.AGENT, "agent-a", ("security:write",), scope
        )
    token = platform.issue_token(
        TokenKind.AGENT, "agent-a", ("incident:read",), scope
    )
    assert token.active
    platform.revoke_token(token.id, scope)
    assert not token.active
    session = platform.create_session("alice", scope)
    with pytest.raises(PermissionError, match="concurrency"):
        platform.create_session("alice", scope)
    platform.revoke_session(session.id, scope)
    assert platform.metrics.snapshot()["active_sessions_total"] == 0


def test_secret_key_encryption_references_rotation_and_no_credentials() -> None:
    platform, scope = configured()
    reference = platform.add_secret_reference(
        SecretReference("database", "vault", "vault://prod/database"), scope
    )
    assert reference.to_dict()["path"] == "vault://prod/database"
    rotated = platform.rotate_secret("database", RotationAdapter(), scope)
    assert rotated.version == "version-2"
    platform.add_key(
        KeyReference("key-a", "kms", "kms://prod/key-a", "AES-256-GCM"),
        RotationPolicy(90),
        scope,
    )
    assert platform.metrics.snapshot()["secret_rotations_total"] == 1
    with pytest.raises(ValueError):
        SecretReference("bad", "inline", "hardcoded-secret")


def test_threat_incident_compliance_audit_dashboard_and_metrics() -> None:
    platform, scope = configured()
    platform.record_threat("rate_limit", IncidentSeverity.MEDIUM, scope, "alice")
    incident = platform.create_incident(
        "incident-a", "Suspicious activity", IncidentSeverity.HIGH, scope, "alice"
    )
    platform.update_incident(
        incident.id,
        scope,
        containment="session revoked",
        resolution="credential rotated",
        postmortem="control improvements tracked",
        status="resolved",
    )
    platform.add_compliance_mapping(
        ComplianceMapping("mapping-a", "policy-a", "ISO 27001", "A.5", 365), scope
    )
    dashboard = platform.dashboard(scope)
    assert dashboard["incidents"][0]["status"] == "resolved"
    assert dashboard["compliance"]["mappings"] == 1
    assert platform.export_audit(scope)
    assert set(platform.metrics.snapshot()) == set(METRICS)
    rendered = platform.metrics.render_prometheus()
    assert all(name in rendered for name in METRICS)
