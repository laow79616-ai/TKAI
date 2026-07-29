"""Enterprise AI Governance Platform facade."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Protocol, TypeVar, cast
from uuid import uuid4

from .dashboard import SECTIONS
from .entities import (
    Approval,
    ComplianceRecord,
    Control,
    Evidence,
    GovernancePolicy,
    GovernanceScope,
    GovernanceScopeType,
    GovernanceStatus,
    GovernedResource,
    Incident,
    PolicyException,
    PolicyStatus,
    Risk,
    Severity,
)
from .metrics import GovernanceMetrics
from .security import GovernanceSecurity


class ScopedRecord(Protocol):
    tenant: str
    workspace: str


T = TypeVar("T", bound=ScopedRecord)

POLICY_TRANSITIONS = {
    PolicyStatus.DRAFT: {PolicyStatus.REVIEW, PolicyStatus.ARCHIVED},
    PolicyStatus.REVIEW: {
        PolicyStatus.DRAFT,
        PolicyStatus.APPROVED,
        PolicyStatus.ARCHIVED,
    },
    PolicyStatus.APPROVED: {PolicyStatus.ACTIVE, PolicyStatus.ARCHIVED},
    PolicyStatus.ACTIVE: {PolicyStatus.SUSPENDED, PolicyStatus.DEPRECATED},
    PolicyStatus.SUSPENDED: {PolicyStatus.ACTIVE, PolicyStatus.DEPRECATED},
    PolicyStatus.DEPRECATED: {PolicyStatus.ARCHIVED},
    PolicyStatus.ARCHIVED: set(),
}

RESOURCE_KINDS = {
    "model",
    "prompt",
    "agent",
    "application",
    "workflow",
    "dataset",
    "knowledge_base",
}
APPROVAL_TYPES = {
    "policy",
    "model",
    "prompt",
    "agent",
    "application",
    "workflow",
    "dataset",
    "exception",
}
CONTROL_TYPES = {
    "access_control",
    "data_boundary",
    "execution_limits",
    "tool_permission",
    "model_allowlist",
    "provider_allowlist",
    "prompt_policy",
    "content_policy",
    "retention_policy",
    "audit_policy",
}


class EnterpriseAIGovernancePlatform:
    """Manage scoped governance records without asserting legal compliance."""

    def __init__(self) -> None:
        self.security = GovernanceSecurity()
        self.metrics = GovernanceMetrics()
        self.policies: dict[str, GovernancePolicy] = {}
        self.risks: dict[str, Risk] = {}
        self.compliance: dict[str, ComplianceRecord] = {}
        self.approvals: dict[str, Approval] = {}
        self.controls: dict[str, Control] = {}
        self.resources: dict[str, GovernedResource] = {}
        self.incidents: dict[str, Incident] = {}
        self.exceptions: dict[str, PolicyException] = {}
        self.evidence: dict[str, Evidence] = {}

    def create_policy(
        self, payload: dict[str, Any], scope: GovernanceScope
    ) -> GovernancePolicy:
        self.security.require(scope, "governance:policy:write")
        item = GovernancePolicy(
            id=str(payload.get("id") or uuid4()),
            tenant=scope.tenant,
            workspace=scope.workspace,
            name=str(payload["name"]),
            description=str(payload.get("description", "")),
            scope_type=GovernanceScopeType(str(payload["scope_type"])),
            scope_id=str(payload.get("scope_id") or scope.workspace),
            owner=str(payload.get("owner") or scope.actor),
            version=str(payload.get("version", "1.0.0")),
            rules=tuple(dict(value) for value in payload.get("rules", ())),
            controls=self._strings(payload.get("controls", ())),
            metadata=dict(payload.get("metadata", {})),
        )
        self._add(self.policies, item.id, item, "Policy")
        self.metrics.increment("governance_policies_total")
        return item

    def transition_policy(
        self, policy_id: str, status: str, scope: GovernanceScope
    ) -> GovernancePolicy:
        self.security.require(scope, "governance:policy:approve")
        item = self._get(self.policies, policy_id, scope)
        target = PolicyStatus(status)
        if target not in POLICY_TRANSITIONS[item.status]:
            raise ValueError(
                f"Invalid policy transition: {item.status.value} -> {target.value}."
            )
        was_active = item.status is PolicyStatus.ACTIVE
        updated = replace(item, status=target)
        self.policies[item.id] = updated
        if was_active != (target is PolicyStatus.ACTIVE):
            self.metrics.increment(
                "governance_active_policies", -1 if was_active else 1
            )
        return updated

    def create_risk(self, payload: dict[str, Any], scope: GovernanceScope) -> Risk:
        self.security.require(scope, "governance:risk:write")
        item = Risk(
            id=str(payload.get("id") or uuid4()),
            tenant=scope.tenant,
            workspace=scope.workspace,
            category=str(payload["category"]),
            likelihood=Severity(str(payload["likelihood"])),
            impact=Severity(str(payload["impact"])),
            severity=Severity(str(payload["severity"])),
            owner=str(payload.get("owner") or scope.actor),
            mitigation=str(payload.get("mitigation", "")),
            residual_risk=Severity(str(payload.get("residual_risk", "medium"))),
            status=GovernanceStatus(str(payload.get("status", "active"))),
        )
        self._add(self.risks, item.id, item, "Risk")
        self.metrics.increment("governance_risks_total")
        if item.severity in {Severity.HIGH, Severity.CRITICAL}:
            self.metrics.increment("governance_high_risks_total")
        return item

    def create_compliance_record(
        self, payload: dict[str, Any], scope: GovernanceScope
    ) -> ComplianceRecord:
        self.security.require(scope, "governance:compliance:write")
        item = ComplianceRecord(
            id=str(payload.get("id") or uuid4()),
            tenant=scope.tenant,
            workspace=scope.workspace,
            framework=str(payload["framework"]),
            control_mapping={
                str(key): str(value)
                for key, value in dict(payload.get("control_mapping", {})).items()
            },
            evidence=self._strings(payload.get("evidence", ())),
            assessment=str(payload.get("assessment", "")),
            finding=str(payload.get("finding", "")),
            remediation=str(payload.get("remediation", "")),
            attestation=str(payload.get("attestation", "")),
            status=GovernanceStatus(str(payload.get("status", "pending"))),
        )
        self._add(self.compliance, item.id, item, "Compliance record")
        if item.finding:
            self.metrics.increment("governance_findings_total")
        return item

    def request_approval(
        self, payload: dict[str, Any], scope: GovernanceScope
    ) -> Approval:
        self.security.require(scope, "governance:approval:request")
        resource_type = str(payload["resource_type"])
        if resource_type not in APPROVAL_TYPES:
            raise ValueError("Unsupported governance approval type.")
        item = Approval(
            id=str(payload.get("id") or uuid4()),
            tenant=scope.tenant,
            workspace=scope.workspace,
            resource_type=resource_type,
            resource_id=str(payload["resource_id"]),
            requested_by=scope.actor,
            reason=str(payload.get("reason", "")),
        )
        self._add(self.approvals, item.id, item, "Approval")
        self.metrics.increment("governance_approvals_total")
        return item

    def decide_approval(
        self, approval_id: str, decision: str, scope: GovernanceScope
    ) -> Approval:
        self.security.require(scope, "governance:approval:decide")
        if decision not in {"approved", "rejected"}:
            raise ValueError("Approval decision must be approved or rejected.")
        item = self._get(self.approvals, approval_id, scope)
        if item.status is not GovernanceStatus.PENDING:
            raise ValueError("Approval has already been decided.")
        updated = replace(item, status=GovernanceStatus(decision), approver=scope.actor)
        self.approvals[item.id] = updated
        return updated

    def create_control(
        self, payload: dict[str, Any], scope: GovernanceScope
    ) -> Control:
        self.security.require(scope, "governance:control:write")
        control_type = str(payload["control_type"])
        if control_type not in CONTROL_TYPES:
            raise ValueError("Unsupported governance control type.")
        item = Control(
            id=str(payload.get("id") or uuid4()),
            tenant=scope.tenant,
            workspace=scope.workspace,
            control_type=control_type,
            name=str(payload["name"]),
            configuration=dict(payload.get("configuration", {})),
        )
        self._add(self.controls, item.id, item, "Control")
        return item

    def register_resource(
        self, kind: str, payload: dict[str, Any], scope: GovernanceScope
    ) -> GovernedResource:
        self.security.require(scope, "governance:resource:write")
        if kind not in RESOURCE_KINDS:
            raise ValueError("Unsupported governed resource type.")
        attributes = dict(payload.get("attributes", {}))
        self._validate_resource_attributes(kind, attributes)
        item = GovernedResource(
            id=str(payload.get("id") or uuid4()),
            tenant=scope.tenant,
            workspace=scope.workspace,
            kind=kind,
            version=str(payload.get("version", "1.0.0")),
            owner=str(payload.get("owner") or scope.actor),
            approval_status=GovernanceStatus(
                str(payload.get("approval_status", "pending"))
            ),
            attributes=attributes,
        )
        key = f"{kind}:{item.id}"
        self._add(self.resources, key, item, "Governed resource")
        return item

    def create_incident(
        self, payload: dict[str, Any], scope: GovernanceScope
    ) -> Incident:
        self.security.require(scope, "governance:incident:write")
        item = Incident(
            id=str(payload.get("id") or uuid4()),
            tenant=scope.tenant,
            workspace=scope.workspace,
            severity=Severity(str(payload["severity"])),
            source=str(payload["source"]),
            affected_resource=str(payload["affected_resource"]),
            owner=str(payload.get("owner") or scope.actor),
            timeline=tuple(dict(value) for value in payload.get("timeline", ())),
            containment=str(payload.get("containment", "")),
            resolution=str(payload.get("resolution", "")),
            postmortem_reference=self._optional(payload.get("postmortem_reference")),
        )
        self._add(self.incidents, item.id, item, "Incident")
        self.metrics.increment("governance_incidents_total")
        return item

    def create_exception(
        self, payload: dict[str, Any], scope: GovernanceScope
    ) -> PolicyException:
        self.security.require(scope, "governance:exception:write")
        policy = self._get(self.policies, str(payload["policy_id"]), scope)
        item = PolicyException(
            id=str(payload.get("id") or uuid4()),
            tenant=scope.tenant,
            workspace=scope.workspace,
            policy_id=policy.id,
            scope=str(payload["scope"]),
            reason=str(payload["reason"]),
            approver=str(payload["approver"]),
            expiration=str(payload["expiration"]),
            compensating_control=str(payload["compensating_control"]),
        )
        self._add(self.exceptions, item.id, item, "Policy exception")
        self.metrics.increment("governance_exceptions_total")
        return item

    def record_evidence(
        self, payload: dict[str, Any], scope: GovernanceScope
    ) -> Evidence:
        self.security.require(scope, "governance:evidence:write")
        item = Evidence(
            id=str(payload.get("id") or uuid4()),
            tenant=scope.tenant,
            workspace=scope.workspace,
            evidence_type=str(payload["evidence_type"]),
            reference=str(payload["reference"]),
            resource_id=str(payload["resource_id"]),
            checksum=str(payload["checksum"]),
        )
        self._add(self.evidence, item.id, item, "Evidence")
        return item

    def list_records(
        self,
        store: dict[str, T],
        scope: GovernanceScope,
        permission: str = "governance:read",
    ) -> tuple[T, ...]:
        self.security.require(scope, permission)
        result: list[T] = []
        for item in store.values():
            tenant = str(item.tenant)
            workspace = str(item.workspace)
            if tenant == scope.tenant and workspace == scope.workspace:
                result.append(item)
        return tuple(result)

    def report(self, scope: GovernanceScope) -> dict[str, Any]:
        self.security.require(scope, "governance:report:read")
        policies = self.list_records(self.policies, scope, "governance:report:read")
        risks = self.list_records(self.risks, scope, "governance:report:read")
        compliance = self.list_records(self.compliance, scope, "governance:report:read")
        return cast(
            dict[str, Any],
            self.security.redact(
                {
                    "policy_coverage": {
                        "total": len(policies),
                        "active": sum(
                            item.status is PolicyStatus.ACTIVE for item in policies
                        ),
                    },
                    "risk_summary": {
                        level.value: sum(item.severity is level for item in risks)
                        for level in Severity
                    },
                    "control_status": self._status_counts(self.controls, scope),
                    "open_findings": sum(bool(item.finding) for item in compliance),
                    "exceptions": len(
                        self.list_records(
                            self.exceptions, scope, "governance:report:read"
                        )
                    ),
                    "incidents": len(
                        self.list_records(
                            self.incidents, scope, "governance:report:read"
                        )
                    ),
                    "approval_status": self._status_counts(self.approvals, scope),
                    "disclaimer": (
                        "Framework mappings and assessments do not constitute "
                        "certification or legal compliance."
                    ),
                },
            ),
        )

    def export_audit(
        self, scope: GovernanceScope, limit: int = 1000
    ) -> list[dict[str, Any]]:
        self.security.require(scope, "governance:report:export")
        if limit < 1 or limit > self.security.max_export_records:
            raise ValueError("Invalid bounded export size.")
        values = [
            item.to_dict()
            for item in self.list_records(
                self.evidence, scope, "governance:report:export"
            )
        ][:limit]
        return self.security.bound_export(values)

    def dashboard(self, scope: GovernanceScope) -> dict[str, Any]:
        self.security.require(scope, "governance:read")
        return {
            "sections": list(SECTIONS),
            "summary": {
                "policies": len(self.list_records(self.policies, scope)),
                "risks": len(self.list_records(self.risks, scope)),
                "approvals": len(self.list_records(self.approvals, scope)),
                "incidents": len(self.list_records(self.incidents, scope)),
            },
            "metrics": self.metrics.snapshot(),
        }

    def _get(self, store: dict[str, T], identifier: str, scope: GovernanceScope) -> T:
        item = store.get(identifier)
        if item is None:
            raise KeyError(identifier)
        self.security.validate_resource(
            str(item.tenant),
            str(item.workspace),
            scope,
        )
        return item

    @staticmethod
    def _add(store: dict[str, T], key: str, item: T, label: str) -> None:
        if key in store:
            raise ValueError(f"{label} already exists.")
        store[key] = item

    @staticmethod
    def _strings(value: Any) -> tuple[str, ...]:
        if isinstance(value, str):
            raise ValueError("Expected a collection, not a string.")
        return tuple(str(item) for item in value)

    @staticmethod
    def _optional(value: Any) -> str | None:
        return None if value is None else str(value)

    def _status_counts(
        self, store: dict[str, Any], scope: GovernanceScope
    ) -> dict[str, int]:
        result: dict[str, int] = {}
        for item in self.list_records(store, scope, "governance:report:read"):
            status = item.status.value
            result[status] = result.get(status, 0) + 1
        return result

    @staticmethod
    def _validate_resource_attributes(kind: str, attributes: dict[str, Any]) -> None:
        requirements = {
            "model": {"provider", "allowed_use", "restricted_use"},
            "prompt": {"risk_classification", "sensitive_variables"},
            "agent": {"tools", "permissions", "memory_policy", "execution_limits"},
            "application": {"components", "permissions", "data_access"},
            "workflow": {"nodes", "connectors", "secrets", "execution_limits"},
            "dataset": {"classification", "retention", "access", "export_policy"},
            "knowledge_base": {
                "classification",
                "retention",
                "access",
                "deletion_policy",
            },
        }
        missing = sorted(requirements[kind] - attributes.keys())
        if missing:
            raise ValueError(
                f"Missing {kind} governance attributes: {', '.join(missing)}."
            )
