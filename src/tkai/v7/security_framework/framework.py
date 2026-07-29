"""In-process V7 security policy evaluation and advisory enforcement metadata."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from threading import RLock
from uuid import uuid4

from tkai.v7.security import filter_secrets

from .contracts import (
    AuditEvent,
    AuthorizationDecision,
    AuthorizationRequest,
    Effect,
    Permission,
    Policy,
    PolicyLifecycle,
    Principal,
    Role,
    SecretReference,
    SecurityScope,
    ValidationIssue,
    ValidationReport,
    serialize,
)

METRIC_NAMES = (
    "v7_security_authorization_total",
    "v7_security_authorization_denied_total",
    "v7_security_policy_evaluations_total",
    "v7_security_policy_conflicts_total",
    "v7_security_compliance_checks_total",
    "v7_security_validation_failures_total",
)


class SecurityFrameworkError(RuntimeError):
    pass


class SecurityValidationError(SecurityFrameworkError):
    pass


class PolicyConflictError(SecurityValidationError):
    pass


class SecurityMetrics:
    def __init__(self) -> None:
        self._values = {name: 0.0 for name in METRIC_NAMES}

    def increment(self, name: str) -> None:
        self._values[name] += 1

    def snapshot(self) -> dict[str, float]:
        return dict(self._values)


class TracingHooks:
    def __init__(self) -> None:
        self._hooks: list[Callable[[str, Mapping[str, object]], None]] = []

    def register(self, hook: Callable[[str, Mapping[str, object]], None]) -> None:
        self._hooks.append(hook)

    def emit(self, name: str, attributes: Mapping[str, object]) -> None:
        safe = filter_secrets(attributes)
        for hook in self._hooks:
            hook(name, safe)


class PolicyRegistry:
    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}
        self._lock = RLock()

    def register(self, policy: Policy) -> Policy:
        with self._lock:
            if policy.policy_id in self._policies:
                raise SecurityValidationError(
                    f"policy already registered: {policy.policy_id}"
                )
            self._policies[policy.policy_id] = policy
        return policy

    def get(self, policy_id: str) -> Policy:
        try:
            return self._policies[policy_id]
        except KeyError as error:
            raise KeyError(f"unknown policy: {policy_id}") from error

    def list(self) -> tuple[Policy, ...]:
        return tuple(
            sorted(
                self._policies.values(),
                key=lambda item: (-item.priority, item.policy_id),
            )
        )


class RbacRegistry:
    def __init__(self) -> None:
        self.permissions: dict[str, Permission] = {}
        self.roles: dict[str, Role] = {}
        self.principals: dict[str, Principal] = {}

    def add_permission(self, permission: Permission) -> Permission:
        if not permission.permission_id.strip() or not permission.capability.strip():
            raise SecurityValidationError("permission ID and capability are required")
        if permission.permission_id in self.permissions:
            raise SecurityValidationError("permission already registered")
        self.permissions[permission.permission_id] = permission
        return permission

    def add_role(self, role: Role) -> Role:
        if not role.role_id.strip():
            raise SecurityValidationError("role ID is required")
        if role.role_id in self.roles:
            raise SecurityValidationError("role already registered")
        if role.role_id in role.parents:
            raise SecurityValidationError("role cannot inherit itself")
        unknown_permissions = role.permissions - self.permissions.keys()
        if unknown_permissions:
            raise SecurityValidationError(
                f"unknown permissions: {', '.join(sorted(unknown_permissions))}"
            )
        unknown_parents = role.parents - self.roles.keys()
        if unknown_parents:
            raise SecurityValidationError(
                f"unknown roles: {', '.join(sorted(unknown_parents))}"
            )
        self.roles[role.role_id] = role
        return role

    def add_principal(self, principal: Principal) -> Principal:
        if not principal.principal_id.strip():
            raise SecurityValidationError("principal ID is required")
        if principal.principal_id in self.principals:
            raise SecurityValidationError("principal already registered")
        unknown_roles = principal.roles - self.roles.keys()
        if unknown_roles:
            raise SecurityValidationError(
                f"unknown roles: {', '.join(sorted(unknown_roles))}"
            )
        self.principals[principal.principal_id] = principal
        return principal

    def resolve_permissions(
        self, role_id: str, visiting: frozenset[str] = frozenset()
    ) -> frozenset[str]:
        if role_id in visiting:
            raise SecurityValidationError("role inheritance cycle")
        try:
            role = self.roles[role_id]
        except KeyError as error:
            raise SecurityValidationError(f"unknown role: {role_id}") from error
        resolved = set(role.permissions)
        for parent in role.parents:
            resolved.update(
                self.resolve_permissions(parent, visiting | frozenset({role_id}))
            )
        unknown = resolved - self.permissions.keys()
        if unknown:
            raise SecurityValidationError(
                f"unknown permissions: {', '.join(sorted(unknown))}"
            )
        return frozenset(resolved)

    def principal_permissions(self, principal: Principal) -> frozenset[str]:
        resolved: set[str] = set()
        for role_id in principal.roles:
            resolved.update(self.resolve_permissions(role_id))
        return frozenset(resolved)

    def principal_roles(self, principal: Principal) -> frozenset[str]:
        resolved: set[str] = set()

        def visit(role_id: str) -> None:
            if role_id in resolved:
                return
            try:
                role = self.roles[role_id]
            except KeyError as error:
                raise SecurityValidationError(f"unknown role: {role_id}") from error
            resolved.add(role_id)
            for parent in role.parents:
                visit(parent)

        for role_id in principal.roles:
            visit(role_id)
        return frozenset(resolved)


class SecretRegistry:
    def __init__(self) -> None:
        self._references: dict[str, SecretReference] = {}

    def register(self, secret: SecretReference) -> SecretReference:
        if secret.secret_id in self._references:
            raise SecurityValidationError("secret reference already registered")
        allowed_schemes = ("env://", "file://", "secret://", "vault-ref://")
        if not secret.reference.startswith(allowed_schemes):
            raise SecurityValidationError("unsupported secret reference scheme")
        if secret.rotation_due_at is not None:
            try:
                datetime.fromisoformat(secret.rotation_due_at)
            except ValueError as error:
                raise SecurityValidationError(
                    "secret rotation date must be ISO-8601"
                ) from error
        serialized = str(serialize(secret.metadata)).lower()
        if any(marker in serialized for marker in ("password", "plaintext", "token")):
            raise SecurityValidationError("secret metadata contains sensitive material")
        self._references[secret.secret_id] = secret
        return secret

    def list(self) -> tuple[SecretReference, ...]:
        return tuple(self._references[key] for key in sorted(self._references))


class SecurityFramework:
    """Central security model with no network calls or secret persistence."""

    def __init__(self) -> None:
        self.policies = PolicyRegistry()
        self.rbac = RbacRegistry()
        self.secrets = SecretRegistry()
        self.metrics = SecurityMetrics()
        self.tracing = TracingHooks()
        self.history: list[AuditEvent] = []
        self.logs: list[dict[str, object]] = []

    def _record(
        self,
        category: str,
        action: str,
        actor: str,
        outcome: str,
        *,
        reference: str | None = None,
        details: Mapping[str, object] | None = None,
    ) -> None:
        safe = filter_secrets(details or {})
        event = AuditEvent(
            str(uuid4()), category, action, actor, outcome, reference, safe
        )
        self.history.append(event)
        self.logs.append(
            {
                "timestamp": event.timestamp,
                "level": "info",
                "event": f"security.{category}.{action}",
                "actor": actor,
                "outcome": outcome,
                "details": safe,
            }
        )

    def register_policy(self, policy: Policy, *, actor: str = "system") -> Policy:
        report = self.validate_policy(policy)
        if not report.valid:
            raise SecurityValidationError(report.issues[0].message)
        registered = self.policies.register(policy)
        self._record(
            "policy", "registered", actor, "success", reference=policy.policy_id
        )
        return registered

    def validate_policy(self, policy: Policy) -> ValidationReport:
        issues: list[ValidationIssue] = []
        if not policy.policy_id.strip():
            issues.append(
                ValidationIssue("policy_id_required", "policy ID is required")
            )
        if not policy.rules:
            issues.append(ValidationIssue("rules_required", "policy requires rules"))
        if not policy.scope.tenant or not policy.scope.workspace:
            issues.append(
                ValidationIssue("scope_required", "tenant and workspace required")
            )
        for rule in policy.rules:
            if rule.permission not in self.rbac.permissions:
                issues.append(
                    ValidationIssue(
                        "unknown_permission",
                        f"unknown permission: {rule.permission}",
                        reference=rule.permission,
                    )
                )
            unknown_roles = rule.roles - self.rbac.roles.keys()
            if unknown_roles:
                issues.append(
                    ValidationIssue(
                        "unknown_role",
                        f"unknown roles: {', '.join(sorted(unknown_roles))}",
                        reference=policy.policy_id,
                    )
                )
        if "7" not in policy.compatible_versions:
            issues.append(ValidationIssue("v7_incompatible", "policy must support V7"))
        return ValidationReport(not issues, tuple(issues))

    def detect_conflicts(self, policy: Policy) -> tuple[str, ...]:
        conflicts: list[str] = []
        for candidate in self.policies.list():
            if (
                candidate.lifecycle is not PolicyLifecycle.ACTIVE
                or candidate.priority != policy.priority
                or candidate.scope != policy.scope
            ):
                continue
            for rule in policy.rules:
                for other in candidate.rules:
                    if (
                        rule.permission == other.permission
                        and rule.effect != other.effect
                    ):
                        conflicts.append(candidate.policy_id)
        return tuple(sorted(set(conflicts)))

    def _scope_allowed(
        self, principal: Principal, requested: SecurityScope
    ) -> tuple[bool, str]:
        if principal.tenant is not None and principal.tenant != requested.tenant:
            return False, "tenant isolation violation"
        if (
            principal.workspace is not None
            and principal.workspace != requested.workspace
        ):
            return False, "workspace isolation violation"
        return True, "scope valid"

    def authorize(self, request: AuthorizationRequest) -> AuthorizationDecision:
        self.metrics.increment("v7_security_authorization_total")
        scope_allowed, scope_reason = self._scope_allowed(
            request.principal, request.scope
        )
        if not scope_allowed:
            return self._decision(request, False, scope_reason)
        if (
            request.capability
            and request.scope.capability
            and request.capability != request.scope.capability
        ):
            return self._decision(request, False, "capability isolation violation")
        if (
            request.service
            and request.scope.service
            and request.service != request.scope.service
        ):
            return self._decision(request, False, "service isolation violation")
        try:
            granted = self.rbac.principal_permissions(request.principal)
        except SecurityValidationError as error:
            return self._decision(request, False, str(error))
        if request.permission not in granted:
            return self._decision(request, False, "permission denied by RBAC")
        return self.evaluate(request)

    def evaluate(self, request: AuthorizationRequest) -> AuthorizationDecision:
        self.metrics.increment("v7_security_policy_evaluations_total")
        matches: list[tuple[Policy, Effect]] = []
        principal_roles = self.rbac.principal_roles(request.principal)
        for policy in self.policies.list():
            if policy.lifecycle is not PolicyLifecycle.ACTIVE:
                continue
            if (
                policy.scope.tenant != request.scope.tenant
                or policy.scope.workspace != request.scope.workspace
            ):
                continue
            for rule in policy.rules:
                role_match = not rule.roles or bool(rule.roles & principal_roles)
                principal_match = (
                    not rule.principals
                    or request.principal.principal_id in rule.principals
                )
                conditions_match = all(
                    request.context.get(key) == value
                    for key, value in rule.conditions.items()
                )
                if (
                    rule.permission == request.permission
                    and role_match
                    and principal_match
                    and conditions_match
                ):
                    matches.append((policy, rule.effect))
        if not matches:
            return self._decision(request, False, "no matching active policy")
        top_priority = max(policy.priority for policy, _ in matches)
        resolved = [
            (policy, effect)
            for policy, effect in matches
            if policy.priority == top_priority
        ]
        effects = {effect for _, effect in resolved}
        conflicts = (
            tuple(policy.policy_id for policy, _ in resolved)
            if len(effects) > 1
            else ()
        )
        if conflicts:
            self.metrics.increment("v7_security_policy_conflicts_total")
        allowed = effects == {Effect.ALLOW}
        reason = (
            "conflicting policies resolved deny-by-default"
            if conflicts
            else "allowed by policy"
            if allowed
            else "denied by policy"
        )
        return self._decision(
            request,
            allowed,
            reason,
            tuple(policy.policy_id for policy, _ in resolved),
            conflicts,
        )

    def _decision(
        self,
        request: AuthorizationRequest,
        allowed: bool,
        reason: str,
        matched: tuple[str, ...] = (),
        conflicts: tuple[str, ...] = (),
    ) -> AuthorizationDecision:
        if not allowed:
            self.metrics.increment("v7_security_authorization_denied_total")
        decision = AuthorizationDecision(
            allowed,
            reason,
            request.principal.principal_id,
            request.permission,
            matched,
            conflicts,
        )
        self._record(
            "authorization",
            "evaluated",
            request.principal.principal_id,
            "allow" if allowed else "deny",
            details={"permission": request.permission, "reason": reason},
        )
        self.tracing.emit(
            "security.authorization.evaluated",
            {"principal": request.principal.principal_id, "allowed": allowed},
        )
        return decision

    def compliance(self) -> ValidationReport:
        self.metrics.increment("v7_security_compliance_checks_total")
        issues: list[ValidationIssue] = []
        recommendations: list[str] = []
        for policy in self.policies.list():
            report = self.validate_policy(policy)
            issues.extend(report.issues)
            conflicts = self.detect_conflicts(policy)
            if conflicts:
                issues.append(
                    ValidationIssue(
                        "policy_conflict",
                        f"policy conflicts with {', '.join(conflicts)}",
                        reference=policy.policy_id,
                    )
                )
        if not self.policies.list():
            recommendations.append("register explicit deny-by-default policies")
        if not self.history:
            recommendations.append("retain local security audit history")
        if issues:
            self.metrics.increment("v7_security_validation_failures_total")
        return ValidationReport(not issues, tuple(issues), tuple(recommendations))

    def validate_configuration(
        self, configuration: Mapping[str, object], *, actor: str = "system"
    ) -> ValidationReport:
        unsafe = [
            key
            for key, value in configuration.items()
            if any(
                marker in key.lower()
                for marker in ("secret", "password", "token", "credential")
            )
            and value != "[REDACTED]"
            and not (isinstance(value, str) and "://" in value)
        ]
        issues = tuple(
            ValidationIssue(
                "plaintext_configuration_secret",
                f"configuration value must be an opaque reference: {key}",
                reference=key,
            )
            for key in sorted(unsafe)
        )
        report = ValidationReport(not issues, issues)
        self._record(
            "configuration",
            "validated",
            actor,
            "success" if report.valid else "failure",
            details={"valid": report.valid, "issues": len(issues)},
        )
        return report

    def validate_integrity(
        self,
        expected: Mapping[str, str],
        observed: Mapping[str, str],
        *,
        actor: str = "system",
    ) -> ValidationReport:
        mismatches = tuple(
            key for key in sorted(expected) if observed.get(key) != expected[key]
        )
        issues = tuple(
            ValidationIssue(
                "integrity_mismatch",
                f"integrity value does not match: {key}",
                reference=key,
            )
            for key in mismatches
        )
        report = ValidationReport(not issues, issues)
        self._record(
            "integrity",
            "validated",
            actor,
            "success" if report.valid else "failure",
            details={"valid": report.valid, "issues": len(issues)},
        )
        return report

    def audit_compliance(self) -> ValidationReport:
        categories = {event.category for event in self.history}
        issues: tuple[ValidationIssue, ...] = ()
        recommendations: tuple[str, ...] = ()
        if not categories:
            issues = (
                ValidationIssue(
                    "audit_history_empty", "security audit history is empty"
                ),
            )
            recommendations = ("retain authorization and policy audit events",)
        return ValidationReport(not issues, issues, recommendations)

    def recommendations(self) -> tuple[str, ...]:
        return self.compliance().recommendations

    def redact(self, values: Mapping[str, object]) -> dict[str, object]:
        return filter_secrets(values)

    def snapshot(self) -> dict[str, object]:
        compliance = self.compliance()
        policies = self.policies.list()
        secrets = self.secrets.list()
        return {
            "policies": serialize(policies),
            "roles": serialize(
                tuple(self.rbac.roles[key] for key in sorted(self.rbac.roles))
            ),
            "permissions": serialize(
                tuple(
                    self.rbac.permissions[key] for key in sorted(self.rbac.permissions)
                )
            ),
            "authorization": {
                "mode": "deny-by-default",
                "reference_only": True,
                "remote_services_enabled": False,
            },
            "compliance": serialize(compliance),
            "secrets": serialize(secrets),
            "audit": serialize(tuple(self.history)),
            "health": {
                "status": "healthy" if compliance.valid else "degraded",
                "policies": len(policies),
                "roles": len(self.rbac.roles),
                "secret_references": len(secrets),
                "plaintext_persistence_enabled": False,
                "remote_security_services_enabled": False,
            },
            "metrics": self.metrics.snapshot(),
        }


GLOBAL_SECURITY_FRAMEWORK = SecurityFramework()

__all__ = (
    "GLOBAL_SECURITY_FRAMEWORK",
    "METRIC_NAMES",
    "PolicyConflictError",
    "PolicyRegistry",
    "RbacRegistry",
    "SecretRegistry",
    "SecurityFramework",
    "SecurityFrameworkError",
    "SecurityMetrics",
    "SecurityValidationError",
    "TracingHooks",
)
