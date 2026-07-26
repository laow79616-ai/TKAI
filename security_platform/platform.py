"""Tenant-scoped Enterprise AI Security Platform domain services.

The implementation is dependency-free and keeps credentials outside the domain
model. Authentication protocols and cryptographic providers are host adapters.
"""

from __future__ import annotations

import hashlib
import secrets as secure_random
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Protocol

from .metrics import SecurityMetrics


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IdentityKind(str, Enum):
    USER = "user"
    SERVICE_ACCOUNT = "service_account"
    AGENT = "agent"
    APPLICATION = "application"
    WORKSPACE = "workspace"
    TENANT = "tenant"


class TokenKind(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    SERVICE = "service"
    AGENT = "agent"


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class SecurityScope:
    tenant: str
    workspace: str
    actor: str

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class Identity:
    id: str
    kind: IdentityKind
    tenant: str
    workspace: str
    display_name: str
    enabled: bool = True
    attributes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["kind"] = self.kind.value
        return value


@dataclass(frozen=True, slots=True)
class AuthenticationRequest:
    method: str
    identity_id: str
    credential: str = field(repr=False)
    tenant: str = ""
    workspace: str = ""
    mfa_code: str | None = field(default=None, repr=False)


@dataclass(frozen=True, slots=True)
class AuthenticationResult:
    authenticated: bool
    identity_id: str
    method: str
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PasswordAuthenticator(Protocol):
    def verify(self, identity_id: str, password: str) -> bool: ...


class OIDCProvider(Protocol):
    def validate(self, token: str) -> dict[str, Any]: ...


class OAuth2Provider(OIDCProvider, Protocol):
    pass


class LDAPProvider(Protocol):
    def bind(self, identity_id: str, password: str) -> bool: ...


class SAMLProvider(Protocol):
    def validate_assertion(self, assertion: str) -> dict[str, Any]: ...


class MFAProvider(Protocol):
    def verify(self, identity_id: str, code: str) -> bool: ...


class Authenticator(Protocol):
    def authenticate(self, request: AuthenticationRequest) -> AuthenticationResult: ...


@dataclass(frozen=True, slots=True)
class PermissionSet:
    id: str
    permissions: frozenset[str]
    description: str = ""


@dataclass(frozen=True, slots=True)
class RoleBinding:
    identity_id: str
    role: str
    tenant: str
    workspace: str


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reason: str
    policy_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ABACPolicy(Protocol):
    def evaluate(
        self, identity: Identity, action: str, resource: str, context: dict[str, Any]
    ) -> PolicyDecision: ...


@dataclass(frozen=True, slots=True)
class Delegation:
    id: str
    grantor: str
    grantee: str
    permissions: frozenset[str]
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class SecretReference:
    name: str
    provider: str
    path: str
    version: str | None = None

    def __post_init__(self) -> None:
        if not self.path or "://" not in self.path:
            raise ValueError("Secret path must be an external provider reference.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class VaultProvider(Protocol):
    def resolve(self, reference: SecretReference) -> str: ...
    def rotate(self, reference: SecretReference) -> str: ...


class SecretRotationProvider(Protocol):
    def rotate(self, reference: SecretReference) -> SecretReference: ...


@dataclass(frozen=True, slots=True)
class KeyReference:
    id: str
    provider: str
    path: str
    algorithm: str


@dataclass(frozen=True, slots=True)
class RotationPolicy:
    interval_days: int
    grace_period_days: int = 7

    def __post_init__(self) -> None:
        if self.interval_days <= 0 or self.grace_period_days < 0:
            raise ValueError("Invalid rotation policy.")


class AtRestEncryption(Protocol):
    def encrypt(self, plaintext: bytes, key: KeyReference) -> bytes: ...
    def decrypt(self, ciphertext: bytes, key: KeyReference) -> bytes: ...


class InTransitEncryption(Protocol):
    def validate_channel(self, endpoint: str) -> bool: ...


@dataclass(slots=True)
class SecurityToken:
    id: str
    kind: TokenKind
    subject: str
    tenant: str
    workspace: str
    scopes: tuple[str, ...]
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None

    @property
    def active(self) -> bool:
        return self.revoked_at is None and utcnow() < self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "kind": self.kind.value,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "active": self.active,
        }


@dataclass(slots=True)
class Session:
    id: str
    identity_id: str
    tenant: str
    workspace: str
    created_at: datetime
    last_active_at: datetime
    idle_timeout: timedelta
    absolute_timeout: timedelta
    revoked_at: datetime | None = None

    @property
    def active(self) -> bool:
        now = utcnow()
        return (
            self.revoked_at is None
            and now - self.last_active_at < self.idle_timeout
            and now - self.created_at < self.absolute_timeout
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "tenant": self.tenant,
            "workspace": self.workspace,
            "created_at": self.created_at.isoformat(),
            "last_active_at": self.last_active_at.isoformat(),
            "active": self.active,
        }


@dataclass(frozen=True, slots=True)
class ThreatEvent:
    id: str
    category: str
    severity: IncidentSeverity
    identity_id: str | None
    tenant: str
    workspace: str
    occurred_at: datetime
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["severity"] = self.severity.value
        value["occurred_at"] = self.occurred_at.isoformat()
        return value


class AnomalyDetector(Protocol):
    def detect(self, event: ThreatEvent) -> bool: ...


@dataclass(slots=True)
class IncidentRecord:
    id: str
    title: str
    severity: IncidentSeverity
    tenant: str
    workspace: str
    owner: str | None = None
    status: str = "open"
    timeline: list[dict[str, str]] = field(default_factory=list)
    containment: str | None = None
    resolution: str | None = None
    postmortem: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["severity"] = self.severity.value
        return value


@dataclass(frozen=True, slots=True)
class ComplianceMapping:
    id: str
    policy_id: str
    framework: str
    control: str
    retention_days: int


@dataclass(frozen=True, slots=True)
class Evidence:
    id: str
    mapping_id: str
    reference: str
    collected_at: datetime


@dataclass(slots=True)
class ComplianceException:
    id: str
    mapping_id: str
    reason: str
    owner: str
    expires_at: datetime
    status: str = "open"


@dataclass(frozen=True, slots=True)
class AuditEvent:
    id: str
    action: str
    actor: str
    tenant: str
    workspace: str
    occurred_at: datetime
    outcome: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["occurred_at"] = self.occurred_at.isoformat()
        return value


class SecurityPlatform:
    """In-memory reference implementation with strict tenant/workspace isolation."""

    METHODS = {"password", "oidc", "oauth2", "ldap", "saml", "api_key", "service_token"}

    def __init__(
        self,
        *,
        idle_timeout: timedelta = timedelta(minutes=30),
        absolute_timeout: timedelta = timedelta(hours=12),
        session_limit: int = 5,
        brute_force_limit: int = 5,
    ) -> None:
        self.identities: dict[str, Identity] = {}
        self.authenticators: dict[str, Authenticator] = {}
        self.permission_sets: dict[str, PermissionSet] = {}
        self.roles: dict[str, frozenset[str]] = {}
        self.bindings: list[RoleBinding] = []
        self.abac_policies: list[ABACPolicy] = []
        self.delegations: dict[str, Delegation] = {}
        self.secret_references: dict[str, SecretReference] = {}
        self.keys: dict[str, KeyReference] = {}
        self.rotation_policies: dict[str, RotationPolicy] = {}
        self.tokens: dict[str, SecurityToken] = {}
        self.sessions: dict[str, Session] = {}
        self.threats: list[ThreatEvent] = []
        self.incidents: dict[str, IncidentRecord] = {}
        self.compliance_mappings: dict[str, ComplianceMapping] = {}
        self.evidence: dict[str, Evidence] = {}
        self.exceptions: dict[str, ComplianceException] = {}
        self.audit_events: list[AuditEvent] = []
        self.metrics = SecurityMetrics()
        self.idle_timeout = idle_timeout
        self.absolute_timeout = absolute_timeout
        self.session_limit = session_limit
        self.brute_force_limit = brute_force_limit
        self._failures: dict[str, deque[datetime]] = defaultdict(deque)
        self._api_keys: dict[str, tuple[str, str]] = {}
        self._service_tokens: dict[str, tuple[str, str]] = {}

    @staticmethod
    def _check_scope(record: Any, scope: SecurityScope) -> None:
        if record.tenant != scope.tenant or record.workspace != scope.workspace:
            raise PermissionError("Cross-scope security access denied.")

    def _audit(
        self, action: str, scope: SecurityScope, outcome: str, **metadata: Any
    ) -> None:
        self.audit_events.append(
            AuditEvent(
                secure_random.token_hex(12),
                action,
                scope.actor,
                scope.tenant,
                scope.workspace,
                utcnow(),
                outcome,
                metadata,
            )
        )
        self.metrics.increment("security_events_total")

    def create_identity(self, identity: Identity, scope: SecurityScope) -> Identity:
        self._check_scope(identity, scope)
        if identity.id in self.identities:
            raise ValueError("Identity already exists.")
        self.identities[identity.id] = identity
        self._audit("identity.create", scope, "success", identity_id=identity.id)
        return identity

    def list_identities(self, scope: SecurityScope) -> list[Identity]:
        return [
            item
            for item in self.identities.values()
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def bind_authenticator(self, method: str, authenticator: Authenticator) -> None:
        if method not in self.METHODS:
            raise ValueError(f"Unsupported authentication method: {method}")
        self.authenticators[method] = authenticator

    @staticmethod
    def _hash_credential(credential: str) -> str:
        return hashlib.sha256(credential.encode()).hexdigest()

    def register_api_key(self, identity_id: str, key: str) -> None:
        self._api_keys[self._hash_credential(key)] = (identity_id, "api_key")

    def register_service_token(self, identity_id: str, token: str) -> None:
        self._service_tokens[self._hash_credential(token)] = (
            identity_id,
            "service_token",
        )

    def authenticate(self, request: AuthenticationRequest) -> AuthenticationResult:
        identity = self.identities.get(request.identity_id)
        scope = SecurityScope(request.tenant, request.workspace, request.identity_id)
        if identity is None or not identity.enabled:
            return self._authentication_failure(request, scope, "identity unavailable")
        self._check_scope(identity, scope)
        if self._brute_force_blocked(identity.id):
            return self._authentication_failure(request, scope, "temporarily blocked")
        if request.method == "api_key":
            expected = self._api_keys.get(self._hash_credential(request.credential))
            valid = expected == (identity.id, "api_key")
            result = AuthenticationResult(valid, identity.id, request.method)
        elif request.method == "service_token":
            expected = self._service_tokens.get(
                self._hash_credential(request.credential)
            )
            valid = expected == (identity.id, "service_token")
            result = AuthenticationResult(valid, identity.id, request.method)
        else:
            adapter = self.authenticators.get(request.method)
            if adapter is None:
                return self._authentication_failure(
                    request, scope, "method not configured"
                )
            result = adapter.authenticate(request)
        if not result.authenticated:
            return self._authentication_failure(
                request, scope, result.reason or "invalid credentials"
            )
        self._failures.pop(identity.id, None)
        self._audit("authentication", scope, "success", method=request.method)
        return result

    def _authentication_failure(
        self, request: AuthenticationRequest, scope: SecurityScope, reason: str
    ) -> AuthenticationResult:
        self._failures[request.identity_id].append(utcnow())
        self.metrics.increment("auth_failures_total")
        self._audit("authentication", scope, "failure", method=request.method)
        return AuthenticationResult(False, request.identity_id, request.method, reason)

    def _brute_force_blocked(self, identity_id: str) -> bool:
        cutoff = utcnow() - timedelta(minutes=15)
        failures = self._failures[identity_id]
        while failures and failures[0] < cutoff:
            failures.popleft()
        if len(failures) < self.brute_force_limit:
            return False
        identity = self.identities.get(identity_id)
        if identity:
            self.record_threat(
                "brute_force",
                IncidentSeverity.HIGH,
                SecurityScope(identity.tenant, identity.workspace, identity_id),
                identity_id,
            )
        return True

    def set_role(self, role: str, permissions: set[str]) -> None:
        self.roles[role] = frozenset(permissions)

    def bind_role(self, binding: RoleBinding, scope: SecurityScope) -> None:
        self._check_scope(binding, scope)
        if binding.role not in self.roles:
            raise ValueError("Unknown role.")
        self.bindings.append(binding)
        self._audit("authorization.bind", scope, "success", role=binding.role)

    def delegate(self, delegation: Delegation, scope: SecurityScope) -> None:
        if delegation.grantor != scope.actor:
            raise PermissionError("Only the grantor may create a delegation.")
        granted = self.permissions_for(delegation.grantor, scope)
        if not delegation.permissions <= granted:
            raise PermissionError("Delegation violates least privilege.")
        self.delegations[delegation.id] = delegation
        self._audit("authorization.delegate", scope, "success")

    def permissions_for(self, identity_id: str, scope: SecurityScope) -> frozenset[str]:
        permissions: set[str] = set()
        for binding in self.bindings:
            if (
                binding.identity_id == identity_id
                and binding.tenant == scope.tenant
                and binding.workspace == scope.workspace
            ):
                permissions.update(self.roles[binding.role])
        now = utcnow()
        for delegation in self.delegations.values():
            if delegation.grantee == identity_id and delegation.expires_at > now:
                permissions.update(delegation.permissions)
        return frozenset(permissions)

    def authorize(
        self,
        identity_id: str,
        action: str,
        resource: str,
        scope: SecurityScope,
        context: dict[str, Any] | None = None,
    ) -> PolicyDecision:
        identity = self.identities.get(identity_id)
        if identity is None:
            decision = PolicyDecision(False, "identity unavailable")
        elif action not in self.permissions_for(identity_id, scope):
            decision = PolicyDecision(False, "RBAC permission denied")
        else:
            decision = PolicyDecision(True, "RBAC permission granted")
            for policy in self.abac_policies:
                evaluated = policy.evaluate(identity, action, resource, context or {})
                if not evaluated.allowed:
                    decision = evaluated
                    break
        if not decision.allowed:
            self.metrics.increment("policy_denials_total")
            self.record_threat(
                "policy_violation",
                IncidentSeverity.MEDIUM,
                scope,
                identity_id,
                {"action": action, "resource": resource},
            )
        self._audit("authorization.evaluate", scope, str(decision.allowed).lower())
        return decision

    def add_secret_reference(
        self, reference: SecretReference, scope: SecurityScope
    ) -> SecretReference:
        self.secret_references[reference.name] = reference
        self._audit("secret.reference", scope, "success", name=reference.name)
        return reference

    def rotate_secret(
        self, name: str, provider: SecretRotationProvider, scope: SecurityScope
    ) -> SecretReference:
        rotated = provider.rotate(self.secret_references[name])
        self.secret_references[name] = rotated
        self.metrics.increment("secret_rotations_total")
        self._audit("secret.rotate", scope, "success", name=name)
        return rotated

    def add_key(
        self, key: KeyReference, policy: RotationPolicy, scope: SecurityScope
    ) -> KeyReference:
        if "://" not in key.path:
            raise ValueError("Key path must be an external provider reference.")
        self.keys[key.id] = key
        self.rotation_policies[key.id] = policy
        self._audit("key.reference", scope, "success", key_id=key.id)
        return key

    def issue_token(
        self,
        kind: TokenKind,
        subject: str,
        scopes: tuple[str, ...],
        scope: SecurityScope,
        lifetime: timedelta = timedelta(minutes=15),
    ) -> SecurityToken:
        allowed = self.permissions_for(subject, scope)
        if not set(scopes) <= allowed:
            raise PermissionError("Token scopes violate least privilege.")
        now = utcnow()
        token = SecurityToken(
            secure_random.token_urlsafe(24),
            kind,
            subject,
            scope.tenant,
            scope.workspace,
            scopes,
            now,
            now + lifetime,
        )
        self.tokens[token.id] = token
        self._audit("token.issue", scope, "success", kind=kind.value)
        return token

    def revoke_token(self, token_id: str, scope: SecurityScope) -> None:
        token = self.tokens[token_id]
        self._check_scope(token, scope)
        token.revoked_at = utcnow()
        self._audit("token.revoke", scope, "success")

    def create_session(self, identity_id: str, scope: SecurityScope) -> Session:
        active = [
            item
            for item in self.sessions.values()
            if item.identity_id == identity_id
            and item.tenant == scope.tenant
            and item.workspace == scope.workspace
            and item.active
        ]
        if len(active) >= self.session_limit:
            raise PermissionError("Session concurrency limit reached.")
        now = utcnow()
        session = Session(
            secure_random.token_urlsafe(24),
            identity_id,
            scope.tenant,
            scope.workspace,
            now,
            now,
            self.idle_timeout,
            self.absolute_timeout,
        )
        self.sessions[session.id] = session
        self._update_active_sessions()
        self._audit("session.create", scope, "success")
        return session

    def touch_session(self, session_id: str, scope: SecurityScope) -> Session:
        session = self.sessions[session_id]
        self._check_scope(session, scope)
        if not session.active:
            raise PermissionError("Session expired or revoked.")
        session.last_active_at = utcnow()
        return session

    def revoke_session(self, session_id: str, scope: SecurityScope) -> None:
        session = self.sessions[session_id]
        self._check_scope(session, scope)
        session.revoked_at = utcnow()
        self._update_active_sessions()
        self._audit("session.revoke", scope, "success")

    def _update_active_sessions(self) -> None:
        self.metrics.set(
            "active_sessions_total",
            sum(1 for session in self.sessions.values() if session.active),
        )

    def record_threat(
        self,
        category: str,
        severity: IncidentSeverity,
        scope: SecurityScope,
        identity_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> ThreatEvent:
        event = ThreatEvent(
            secure_random.token_hex(12),
            category,
            severity,
            identity_id,
            scope.tenant,
            scope.workspace,
            utcnow(),
            details or {},
        )
        self.threats.append(event)
        self.metrics.increment("security_events_total")
        return event

    def create_incident(
        self,
        incident_id: str,
        title: str,
        severity: IncidentSeverity,
        scope: SecurityScope,
        owner: str | None = None,
    ) -> IncidentRecord:
        incident = IncidentRecord(
            incident_id,
            title,
            severity,
            scope.tenant,
            scope.workspace,
            owner,
            timeline=[{"at": utcnow().isoformat(), "event": "created"}],
        )
        self.incidents[incident.id] = incident
        self.metrics.increment("incident_total")
        self._audit("incident.create", scope, "success", incident_id=incident.id)
        return incident

    def update_incident(
        self,
        incident_id: str,
        scope: SecurityScope,
        *,
        status: str | None = None,
        owner: str | None = None,
        containment: str | None = None,
        resolution: str | None = None,
        postmortem: str | None = None,
    ) -> IncidentRecord:
        incident = self.incidents[incident_id]
        self._check_scope(incident, scope)
        for name, value in {
            "status": status,
            "owner": owner,
            "containment": containment,
            "resolution": resolution,
            "postmortem": postmortem,
        }.items():
            if value is not None:
                setattr(incident, name, value)
                incident.timeline.append(
                    {"at": utcnow().isoformat(), "event": f"{name} updated"}
                )
        self._audit("incident.update", scope, "success", incident_id=incident.id)
        return incident

    def add_compliance_mapping(
        self, mapping: ComplianceMapping, scope: SecurityScope
    ) -> ComplianceMapping:
        self.compliance_mappings[mapping.id] = mapping
        self._audit("compliance.mapping", scope, "success")
        return mapping

    def add_evidence(self, evidence: Evidence, scope: SecurityScope) -> Evidence:
        if evidence.mapping_id not in self.compliance_mappings:
            raise ValueError("Unknown compliance mapping.")
        self.evidence[evidence.id] = evidence
        self._audit("compliance.evidence", scope, "success")
        return evidence

    def export_audit(
        self, scope: SecurityScope, since: datetime | None = None
    ) -> list[dict[str, Any]]:
        return [
            event.to_dict()
            for event in self.audit_events
            if event.tenant == scope.tenant
            and event.workspace == scope.workspace
            and (since is None or event.occurred_at >= since)
        ]

    def dashboard(self, scope: SecurityScope) -> dict[str, Any]:
        self._update_active_sessions()
        scoped_identities = self.list_identities(scope)
        return {
            "identity": {"total": len(scoped_identities)},
            "authentication": {
                "failures": self.metrics.snapshot()["auth_failures_total"]
            },
            "authorization": {
                "denials": self.metrics.snapshot()["policy_denials_total"]
            },
            "secrets": {"references": len(self.secret_references)},
            "threats": [
                item.to_dict()
                for item in self.threats
                if item.tenant == scope.tenant and item.workspace == scope.workspace
            ],
            "incidents": [
                item.to_dict()
                for item in self.incidents.values()
                if item.tenant == scope.tenant and item.workspace == scope.workspace
            ],
            "compliance": {
                "mappings": len(self.compliance_mappings),
                "evidence": len(self.evidence),
                "exceptions": len(self.exceptions),
            },
            "audit": self.export_audit(scope),
            "metrics": self.metrics.snapshot(),
        }


EnterpriseAISecurityPlatform = SecurityPlatform

__all__ = (
    "ABACPolicy",
    "AnomalyDetector",
    "AtRestEncryption",
    "AuditEvent",
    "AuthenticationRequest",
    "AuthenticationResult",
    "Authenticator",
    "ComplianceException",
    "ComplianceMapping",
    "Delegation",
    "EnterpriseAISecurityPlatform",
    "Evidence",
    "Identity",
    "IdentityKind",
    "IncidentRecord",
    "IncidentSeverity",
    "InTransitEncryption",
    "KeyReference",
    "LDAPProvider",
    "MFAProvider",
    "OAuth2Provider",
    "OIDCProvider",
    "PasswordAuthenticator",
    "PermissionSet",
    "PolicyDecision",
    "RoleBinding",
    "RotationPolicy",
    "SAMLProvider",
    "SecretReference",
    "SecretRotationProvider",
    "SecurityPlatform",
    "SecurityScope",
    "SecurityToken",
    "Session",
    "ThreatEvent",
    "TokenKind",
    "VaultProvider",
    "utcnow",
)
