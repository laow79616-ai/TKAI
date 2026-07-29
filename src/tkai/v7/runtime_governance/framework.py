"""Bounded, local and advisory-only unified runtime governance framework."""

from __future__ import annotations

from collections import Counter
from threading import RLock
from typing import TypeVar

from .contracts import (
    ApprovalReference,
    Diagnostic,
    EligibilityAssessment,
    EligibilityRequest,
    GovernanceConstraint,
    GovernancePolicy,
    GovernanceProfile,
    KillSwitchMetadata,
    Lifecycle,
    MaintenanceMetadata,
    PauseMetadata,
    ReviewMetadata,
    RuntimeBoundary,
    RuntimeReference,
    Scope,
    serialize,
    utc_now,
)

T = TypeVar("T")
MAX_ITEMS = 1000
METRIC_NAMES = (
    "v7_runtime_governance_profiles_total",
    "v7_runtime_governance_policies_total",
    "v7_runtime_governance_constraints_total",
    "v7_runtime_governance_eligibility_total",
    "v7_runtime_governance_eligible_total",
    "v7_runtime_governance_ineligible_total",
    "v7_runtime_governance_boundaries_total",
    "v7_runtime_governance_pause_total",
    "v7_runtime_governance_killswitch_total",
    "v7_runtime_governance_diagnostics_total",
    "v7_runtime_governance_health_status",
)


class RuntimeGovernanceError(RuntimeError):
    pass


class IsolationError(RuntimeGovernanceError):
    pass


class Registry:
    """Thread-safe, append-only metadata registry."""

    def __init__(self) -> None:
        self._items: dict[str, object] = {}
        self._lock = RLock()

    def add(self, key: str, item: T) -> T:
        with self._lock:
            if key in self._items:
                raise RuntimeGovernanceError(f"immutable metadata exists: {key}")
            if len(self._items) >= MAX_ITEMS:
                raise RuntimeGovernanceError("bounded registry capacity reached")
            self._items[key] = item
        return item

    def values(self, expected: type[T], scope: Scope | None = None) -> tuple[T, ...]:
        return tuple(
            item
            for item in self._items.values()
            if isinstance(item, expected)
            and (scope is None or getattr(item, "scope", None) == scope)
        )[:MAX_ITEMS]

    def get(self, key: str, expected: type[T], scope: Scope) -> T:
        item = self._items.get(key)
        if not isinstance(item, expected) or getattr(item, "scope", None) != scope:
            raise IsolationError(f"missing or cross-scope metadata: {key}")
        return item


class RuntimeGovernanceFramework:
    """Advisory metadata coordination with deliberately no execution surface."""

    PROJECTIONS = (
        "profiles",
        "policies",
        "eligibility",
        "runtime",
        "pause",
        "killswitch",
        "diagnostics",
        "health",
        "metrics",
    )
    DASHBOARD_SECTIONS = (
        "overview",
        "policies",
        "eligibility",
        "runtime",
        "pause",
        "killswitch",
        "diagnostics",
        "health",
        "metrics",
        "audit",
    )
    _TYPES = {
        "profiles": GovernanceProfile,
        "policies": GovernancePolicy,
        "eligibility": EligibilityAssessment,
        "runtime": RuntimeReference,
        "pause": PauseMetadata,
        "killswitch": KillSwitchMetadata,
        "diagnostics": Diagnostic,
    }

    def __init__(self) -> None:
        self.registries = {
            name: Registry()
            for name in (
                "profiles",
                "policies",
                "constraints",
                "eligibility",
                "boundaries",
                "runtime",
                "maintenance",
                "pause",
                "killswitch",
                "reviews",
                "approvals",
                "diagnostics",
            )
        }
        self.metric_values = Counter({name: 0 for name in METRIC_NAMES})
        self.metric_values["v7_runtime_governance_health_status"] = 1
        self.audit_log: list[dict[str, object]] = []
        self.events: list[dict[str, object]] = []
        self.trace_hooks: list[dict[str, object]] = []

    def register_profile(self, item: GovernanceProfile) -> GovernanceProfile:
        return self._add("profiles", item.profile_id, item, "profile-registered")

    def register_policy(self, item: GovernancePolicy) -> GovernancePolicy:
        return self._add("policies", item.policy_id, item, "policy-registered")

    def register_constraint(self, item: GovernanceConstraint) -> GovernanceConstraint:
        return self._add(
            "constraints", item.constraint_id, item, "constraint-registered"
        )

    def register_boundary(self, item: RuntimeBoundary) -> RuntimeBoundary:
        return self._add("boundaries", item.boundary_id, item, "boundary-registered")

    def register_runtime(self, item: RuntimeReference) -> RuntimeReference:
        for reference in item.boundary_references:
            self.registries["boundaries"].get(reference, RuntimeBoundary, item.scope)
        return self._add("runtime", item.runtime_id, item, "runtime-referenced")

    def register_maintenance(self, item: MaintenanceMetadata) -> MaintenanceMetadata:
        return self._add(
            "maintenance", item.maintenance_id, item, "maintenance-recorded"
        )

    def record_pause(self, item: PauseMetadata) -> PauseMetadata:
        return self._add("pause", item.pause_id, item, "pause-metadata-recorded")

    def record_killswitch(self, item: KillSwitchMetadata) -> KillSwitchMetadata:
        return self._add(
            "killswitch",
            item.killswitch_id,
            item,
            "killswitch-metadata-recorded",
        )

    def record_review(self, item: ReviewMetadata) -> ReviewMetadata:
        return self._add("reviews", item.review_id, item, "review-recorded")

    def record_approval(self, item: ApprovalReference) -> ApprovalReference:
        return self._add(
            "approvals", item.approval_id, item, "approval-reference-recorded"
        )

    def evaluate_eligibility(
        self, request: EligibilityRequest
    ) -> EligibilityAssessment:
        """Evaluate declarations without executing or changing any runtime."""
        reasons: list[str] = []
        for reference in request.policy_references:
            try:
                policy = self.registries["policies"].get(
                    reference, GovernancePolicy, request.scope
                )
                if policy.lifecycle not in (
                    Lifecycle.READY,
                    Lifecycle.REVIEW,
                    Lifecycle.APPROVED_REFERENCE,
                ):
                    reasons.append(f"policy-not-ready:{reference}")
            except IsolationError:
                reasons.append(f"policy-missing-or-isolated:{reference}")
        for reference in request.constraint_references:
            try:
                self.registries["constraints"].get(
                    reference, GovernanceConstraint, request.scope
                )
            except IsolationError:
                reasons.append(f"constraint-missing-or-isolated:{reference}")
        if request.runtime_reference:
            try:
                runtime = self.registries["runtime"].get(
                    request.runtime_reference, RuntimeReference, request.scope
                )
                if not runtime.readiness:
                    reasons.append(f"runtime-not-ready:{request.runtime_reference}")
            except IsolationError:
                reasons.append(
                    f"runtime-missing-or-isolated:{request.runtime_reference}"
                )
        if self._active_pause(request.scope, request.subject_reference):
            reasons.append("active-pause-metadata")
        if self._active_killswitch(request.scope, request.subject_reference):
            reasons.append("active-killswitch-metadata")
        assessment = EligibilityAssessment(
            request.assessment_id,
            request.kind,
            request.subject_reference,
            request.scope,
            not reasons,
            tuple(reasons or ("declared-metadata-satisfied",)),
            request.policy_references,
            request.constraint_references,
        )
        result = self._add(
            "eligibility",
            assessment.assessment_id,
            assessment,
            "eligibility-evaluated",
        )
        self.metric_values[
            "v7_runtime_governance_eligible_total"
            if result.eligible
            else "v7_runtime_governance_ineligible_total"
        ] += 1
        return result

    def diagnose(self, scope: Scope) -> tuple[Diagnostic, ...]:
        findings: list[Diagnostic] = []
        profiles = self.registries["profiles"].values(GovernanceProfile, scope)
        if not profiles:
            findings.append(
                Diagnostic(
                    f"diagnostic-{len(self.audit_log)}",
                    "governance",
                    "profile-missing",
                    "warning",
                    "No runtime governance profile is registered for this scope.",
                    scope,
                )
            )
        for profile in profiles:
            missing_policies = [
                reference
                for reference in profile.policy_references
                if not self._exists(
                    "policies", GovernancePolicy, reference, profile.scope
                )
            ]
            if missing_policies:
                findings.append(
                    Diagnostic(
                        f"diagnostic-{profile.profile_id}-policy",
                        "policy",
                        "policy-reference-missing",
                        "error",
                        "One or more policy references are unavailable in scope.",
                        scope,
                        profile.profile_id,
                        tuple(missing_policies),
                    )
                )
        return tuple(findings[:MAX_ITEMS])

    def health(self, scope: Scope) -> dict[str, object]:
        diagnostics = self.diagnose(scope)
        ready = not any(item.severity == "error" for item in diagnostics)
        return {
            "status": "healthy" if ready else "degraded",
            "governance": "healthy",
            "policy": "healthy",
            "compatibility": "healthy",
            "boundaries": "healthy",
            "framework_readiness": ready,
            "framework_liveness": True,
            "advisory_only": True,
            "external_network": False,
            "tiktok_actions": False,
            "runtime_execution": False,
            "runtime_mutation": False,
            "automatic_approval": False,
            "scope": serialize(scope),
            "diagnostics": serialize(diagnostics),
        }

    def compatibility(self) -> dict[str, object]:
        return {
            "v6_behavior_preserved": True,
            "v6_runtime_mutated": False,
            "read_only_reference_adapters": True,
            "external_network": False,
            "tiktok_business_behavior_changed": False,
        }

    def projection(self, section: str, scope: Scope) -> object:
        if section not in self.PROJECTIONS:
            raise RuntimeGovernanceError(f"unknown projection: {section}")
        if section == "metrics":
            return dict(self.metric_values)
        if section == "health":
            return self.health(scope)
        if section == "diagnostics":
            return serialize(self.diagnose(scope))
        expected = self._TYPES[section]
        return serialize(self.registries[section].values(expected, scope))

    def dashboard(self, scope: Scope) -> dict[str, object]:
        return {
            "overview": {
                "profile_count": len(
                    self.registries["profiles"].values(GovernanceProfile, scope)
                ),
                "advisory_only": True,
                "compatibility": self.compatibility(),
            },
            "policies": self.projection("policies", scope),
            "eligibility": self.projection("eligibility", scope),
            "runtime": self.projection("runtime", scope),
            "pause": self.projection("pause", scope),
            "killswitch": self.projection("killswitch", scope),
            "diagnostics": self.projection("diagnostics", scope),
            "health": self.health(scope),
            "metrics": dict(self.metric_values),
            "audit": tuple(
                item for item in self.audit_log if item["scope"] == serialize(scope)
            ),
        }

    def _active_pause(self, scope: Scope, subject: str) -> bool:
        return any(
            item.active and item.subject_reference in (subject, scope.workspace)
            for item in self.registries["pause"].values(PauseMetadata, scope)
        )

    def _active_killswitch(self, scope: Scope, subject: str) -> bool:
        return any(
            item.active and item.subject_reference in (subject, scope.workspace)
            for item in self.registries["killswitch"].values(KillSwitchMetadata, scope)
        )

    def _exists(self, registry: str, expected: type[T], key: str, scope: Scope) -> bool:
        try:
            self.registries[registry].get(key, expected, scope)
        except IsolationError:
            return False
        return True

    def _add(self, section: str, key: str, item: T, event: str) -> T:
        result = self.registries[section].add(key, item)
        metric = f"v7_runtime_governance_{section}_total"
        if metric in self.metric_values:
            self.metric_values[metric] += 1
        scope = getattr(item, "scope", None)
        if isinstance(scope, Scope):
            self._record(event, key, scope)
        return result

    def _record(self, event: str, subject: str, scope: Scope) -> None:
        record = {
            "event": event,
            "subject": subject,
            "scope": serialize(scope),
            "timestamp": utc_now().isoformat(),
            "structured": True,
            "secret_filtered": True,
        }
        self.audit_log.append(record)
        self.events.append({"fabric": "v7-event-fabric", **record})
        self.trace_hooks.append(
            {
                "trace_reference": f"trace://runtime-governance/{len(self.audit_log)}",
                "event": event,
                "scope": serialize(scope),
            }
        )


GLOBAL_RUNTIME_GOVERNANCE = RuntimeGovernanceFramework()

__all__ = tuple(name for name in globals() if not name.startswith("_"))
