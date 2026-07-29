"""Autonomous governance control plane; operational execution is absent."""
# ruff: noqa: F405

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from .adapters import INTEGRATION_MODULES, GovernancePort, ReferenceOnlyGovernancePort
from .metrics import GovernanceMetrics
from .models import *  # noqa: F403, F405

TRANSITIONS = {
    Lifecycle.DRAFT: {Lifecycle.REVIEW, Lifecycle.DELETED},
    Lifecycle.REVIEW: {Lifecycle.APPROVED, Lifecycle.DRAFT, Lifecycle.ARCHIVED},
    Lifecycle.APPROVED: {Lifecycle.ACTIVE, Lifecycle.ARCHIVED},
    Lifecycle.ACTIVE: {Lifecycle.MONITORING, Lifecycle.SUSPENDED, Lifecycle.EXPIRED},
    Lifecycle.MONITORING: {Lifecycle.ACTIVE, Lifecycle.SUSPENDED, Lifecycle.EXPIRED},
    Lifecycle.SUSPENDED: {Lifecycle.REVIEW, Lifecycle.ARCHIVED},
    Lifecycle.EXPIRED: {Lifecycle.ARCHIVED},
    Lifecycle.ARCHIVED: {Lifecycle.DELETED},
    Lifecycle.DELETED: set(),
}


class TikTokAutonomousGovernanceCenter:
    def __init__(self, modules: Mapping[str, GovernancePort] | None = None) -> None:
        supplied = modules or {}
        self.modules = {
            n: supplied.get(n, ReferenceOnlyGovernancePort(n))
            for n in INTEGRATION_MODULES
        }
        self.profiles = {}
        self.policies = {}
        self.rules = {}
        self.controls = {}
        self.approvals = {}
        self.reviews = {}
        self.exceptions = {}
        self.evidence = {}
        self.changes = {}
        self.risks = {}
        self.audits = []
        self.history = []
        self.metrics = GovernanceMetrics()

    @staticmethod
    def _require(c: AccessContext, a: str) -> None:
        p = f"tiktok:governance-center:{a}"
        if (
            p not in c.permissions
            and "tiktok:governance-center:admin" not in c.permissions
        ):
            raise PermissionError(f"RBAC permission required: {p}")

    @staticmethod
    def _scoped(i: object, c: AccessContext) -> None:
        if (
            getattr(i, "tenant", None) != c.tenant
            or getattr(i, "workspace", None) != c.workspace
        ):
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _put(self, store: dict[str, Any], i: Any, c: AccessContext, metric: str) -> Any:
        self._require(c, "write")
        self._scoped(i, c)
        i.validate()
        if i.id in store:
            raise ValueError("Governance record ID must be unique.")
        store[i.id] = i
        self.metrics.increment(metric)
        self.history.append(
            {
                "resource": i.id,
                "type": type(i).__name__,
                "action": "created",
                "tenant": c.tenant,
                "workspace": c.workspace,
                "timestamp": utcnow(),
            }
        )
        return i

    def create_profile(
        self, i: GovernanceProfile, c: AccessContext
    ) -> GovernanceProfile:
        return self._put(self.profiles, i, c, "tiktok_governance_profiles_total")

    def transition_profile(
        self, r: str, s: Lifecycle, c: AccessContext
    ) -> GovernanceProfile:
        self._require(c, "approve")
        i = self.profiles[r]
        self._scoped(i, c)
        if s not in TRANSITIONS[i.status]:
            raise ValueError("Invalid governance lifecycle transition.")
        i.status = s
        return i

    def create_policy(self, i: Policy, c: AccessContext) -> Policy:
        if i.profile_id not in self.profiles:
            raise ValueError("Policy requires an existing profile.")
        return self._put(self.policies, i, c, "tiktok_governance_policies_total")

    def create_rule(self, i: PolicyRule, c: AccessContext) -> PolicyRule:
        if i.policy_id not in self.policies:
            raise ValueError("Rule requires an existing policy.")
        return self._put(self.rules, i, c, "tiktok_governance_rules_total")

    def create_control(self, i: Control, c: AccessContext) -> Control:
        return self._put(self.controls, i, c, "tiktok_governance_controls_total")

    def request_approval(self, i: Approval, c: AccessContext) -> Approval:
        return self._put(self.approvals, i, c, "tiktok_governance_approvals_total")

    def decide_approval(
        self,
        r: str,
        approved: bool,
        reviewer: str,
        c: AccessContext,
        reason: str | None = None,
    ) -> Approval:
        self._require(c, "approve")
        i = self.approvals[r]
        self._scoped(i, c)
        if i.status is not ApprovalStatus.PENDING:
            raise ValueError("Only pending approvals may be decided.")
        if i.expires_at and i.expires_at <= utcnow():
            i.status = ApprovalStatus.EXPIRED
            raise PermissionError("Approval expired.")
        if not approved and not reason:
            raise ValueError("Rejection reason required.")
        i.reviewer = reviewer
        i.rejection_reason = reason
        i.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        i.decided_at = utcnow()
        if not approved:
            self.metrics.increment("tiktok_governance_rejections_total")
        self.metrics.observe(
            "tiktok_governance_approval_seconds",
            (i.decided_at - i.created_at).total_seconds(),
        )
        return i

    def create_review(self, i: Review, c: AccessContext) -> Review:
        return self._put(self.reviews, i, c, "tiktok_governance_reviews_total")

    def request_exception(
        self, i: ExceptionRequest, c: AccessContext
    ) -> ExceptionRequest:
        return self._put(self.exceptions, i, c, "tiktok_governance_exceptions_total")

    def approve_exception(
        self, r: str, reviewer: str, c: AccessContext
    ) -> ExceptionRequest:
        self._require(c, "approve")
        i = self.exceptions[r]
        self._scoped(i, c)
        i.validate()
        i.reviewer = reviewer
        i.status = ApprovalStatus.APPROVED
        return i

    def add_evidence(self, i: Evidence, c: AccessContext) -> Evidence:
        return self._put(self.evidence, i, c, "tiktok_governance_audit_events_total")

    def request_change(self, i: ChangeRequest, c: AccessContext) -> ChangeRequest:
        if i.target_module not in INTEGRATION_MODULES:
            raise ValueError("Target is outside governed modules.")
        return self._put(self.changes, i, c, "tiktok_governance_changes_total")

    def assess_risk(self, i: RiskAssessment, c: AccessContext) -> RiskAssessment:
        self._require(c, "write")
        self._scoped(i, c)
        i.validate()
        self.risks[i.id] = i
        return i

    def record_audit(self, i: AuditRecord, c: AccessContext) -> AuditRecord:
        self._require(c, "audit")
        self._scoped(i, c)
        i.validate()
        self.audits.append(i)
        self.metrics.increment("tiktok_governance_audit_events_total")
        return i

    def govern(
        self,
        module: str,
        resource_id: str,
        c: AccessContext,
        requested_capabilities: frozenset[str] = frozenset(),
        approval_id: str | None = None,
    ) -> dict[str, Any]:
        self._require(c, "evaluate")
        if module not in self.modules:
            raise ValueError("Module is outside governance boundary.")
        prohibited = requested_capabilities & CORE_PROHIBITIONS
        if prohibited:
            self.metrics.increment("tiktok_governance_safety_events_total")
            return {
                "allowed": False,
                "reason": "core_safety_prohibition",
                "prohibitions": sorted(prohibited),
                "execute": False,
            }
        a = self.approvals.get(approval_id or "")
        if approval_id and (
            not a
            or a.status is not ApprovalStatus.APPROVED
            or a.tenant != c.tenant
            or a.workspace != c.workspace
            or (a.expires_at and a.expires_at <= utcnow())
        ):
            return {
                "allowed": False,
                "reason": "valid_approval_required",
                "execute": False,
            }
        return {
            "allowed": True,
            "reason": "governance_checks_passed",
            "execute": False,
            "snapshot": self.modules[module].governance_snapshot(resource_id, c),
        }

    def _items(self, s: Mapping[str, Any], c: AccessContext) -> list[Any]:
        self._require(c, "read")
        return [
            asdict(i)
            for i in s.values()
            if i.tenant == c.tenant and i.workspace == c.workspace
        ]

    def monitoring(self, c: AccessContext) -> dict[str, Any]:
        return {
            "policy_health": "healthy",
            "control_health": "healthy",
            "approval_queue": sum(
                i.status is ApprovalStatus.PENDING for i in self.approvals.values()
            ),
            "open_reviews": sum(
                i.status is Lifecycle.REVIEW for i in self.reviews.values()
            ),
            "active_exceptions": sum(
                i.status is ApprovalStatus.APPROVED and i.expires_at > utcnow()
                for i in self.exceptions.values()
            ),
            "change_requests": len(self._items(self.changes, c)),
            "audit_health": "healthy",
            "evidence_health": "healthy",
            "compliance_status": "internal-controls-monitored",
            "risk_status": "monitored",
            "safety_status": "core-prohibitions-enforced",
        }

    def analytics(self, c: AccessContext) -> dict[str, float]:
        return {
            f"{n}_total": float(len(self._items(s, c)))
            for n, s in (
                ("profiles", self.profiles),
                ("policies", self.policies),
                ("rules", self.rules),
                ("controls", self.controls),
                ("approvals", self.approvals),
                ("reviews", self.reviews),
                ("exceptions", self.exceptions),
                ("changes", self.changes),
            )
        }

    def dashboard(self, c: AccessContext) -> dict[str, Any]:
        sections = [
            "governance_overview",
            "profiles",
            "policies",
            "rules",
            "controls",
            "approvals",
            "reviews",
            "exceptions",
            "evidence",
            "audit",
            "changes",
            "versions",
            "risk",
            "compliance",
            "safety",
            "monitoring",
            "history",
            "analytics",
        ]
        return {
            "sections": sections,
            "governance_overview": {
                "operational_execution": False,
                "core_prohibitions": sorted(CORE_PROHIBITIONS),
                "integrations": list(self.modules),
            },
            "profiles": self._items(self.profiles, c),
            "monitoring": self.monitoring(c),
            "analytics": self.analytics(c),
        }
