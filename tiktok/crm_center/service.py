"""Consent-aware, non-outreach TikTok CRM orchestration."""

from __future__ import annotations

from dataclasses import asdict
from time import perf_counter
from typing import Any, cast

from .adapters import BoundedTestDouble, ReferencePort, WorkflowHandoffPort
from .metrics import CRMMetrics
from .models import (
    Activity,
    AuditEvent,
    ConsentRecord,
    ConsentStatus,
    Contact,
    CRMRecord,
    CRMScope,
    CRMStatus,
    FollowUp,
    Opportunity,
    Organization,
    Relationship,
    utcnow,
    validate_reference,
)

TRANSITIONS: dict[CRMStatus, frozenset[CRMStatus]] = {
    CRMStatus.NEW: frozenset(
        {CRMStatus.QUALIFIED, CRMStatus.INACTIVE, CRMStatus.ARCHIVED}
    ),
    CRMStatus.QUALIFIED: frozenset(
        {CRMStatus.ACTIVE, CRMStatus.INACTIVE, CRMStatus.ARCHIVED}
    ),
    CRMStatus.ACTIVE: frozenset(
        {CRMStatus.OPPORTUNITY, CRMStatus.INACTIVE, CRMStatus.ARCHIVED}
    ),
    CRMStatus.OPPORTUNITY: frozenset(
        {CRMStatus.NEGOTIATION, CRMStatus.LOST, CRMStatus.INACTIVE}
    ),
    CRMStatus.NEGOTIATION: frozenset(
        {CRMStatus.WON, CRMStatus.LOST, CRMStatus.INACTIVE}
    ),
    CRMStatus.WON: frozenset({CRMStatus.INACTIVE, CRMStatus.ARCHIVED}),
    CRMStatus.LOST: frozenset({CRMStatus.INACTIVE, CRMStatus.ARCHIVED}),
    CRMStatus.INACTIVE: frozenset({CRMStatus.ACTIVE, CRMStatus.ARCHIVED}),
    CRMStatus.ARCHIVED: frozenset({CRMStatus.DELETED}),
    CRMStatus.DELETED: frozenset(),
}


class TikTokCRMCenter:
    def __init__(
        self,
        references: ReferencePort | None = None,
        workflows: WorkflowHandoffPort | None = None,
    ) -> None:
        self.reference_port = references or BoundedTestDouble()
        self.workflow_port = workflows or BoundedTestDouble()
        self.records: dict[str, CRMRecord] = {}
        self.organizations: dict[str, Organization] = {}
        self.contacts: dict[str, Contact] = {}
        self.relationships: dict[str, Relationship] = {}
        self.opportunities: dict[str, Opportunity] = {}
        self.activities: dict[str, Activity] = {}
        self.followups: dict[str, FollowUp] = {}
        self.consents: dict[str, ConsentRecord] = {}
        self.notes: dict[str, dict[str, Any]] = {}
        self.documents: dict[str, dict[str, Any]] = {}
        self.audit: list[AuditEvent] = []
        self.versions: list[dict[str, Any]] = []
        self.metrics = CRMMetrics()

    @staticmethod
    def _require(scope: CRMScope, action: str) -> None:
        permission = f"tiktok:crm:{action}"
        if (
            permission not in scope.permissions
            and "tiktok:crm:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(item: Any, scope: CRMScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def scoped_values(self, values: Any, scope: CRMScope) -> list[Any]:
        self._require(scope, "read")
        return [
            item
            for item in values
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def _record(
        self, crm_id: str, scope: CRMScope, action: str, detail: str = ""
    ) -> None:
        if any(key in detail.casefold() for key in ("token=", "cookie=", "secret=")):
            raise ValueError("Secrets are forbidden in audit events.")
        self.audit.append(
            AuditEvent(
                crm_id, scope.tenant, scope.workspace, scope.actor, action, detail
            )
        )

    def create_record(self, item: CRMRecord, scope: CRMScope) -> CRMRecord:
        started = perf_counter()
        self._require(scope, "write")
        self._scoped(item, scope)
        item.validate()
        if item.id in self.records:
            raise ValueError("CRM ID must be unique.")
        if item.lead_reference:
            self.reference_port.resolve(item.lead_reference, scope)
        self.records[item.id] = item
        self.versions.append(item.to_dict())
        self.metrics.increment("tiktok_crm_records_total")
        self.metrics.set("tiktok_crm_latency_seconds", perf_counter() - started)
        self._record(item.id, scope, "crm.created")
        return item

    def transition(self, crm_id: str, status: CRMStatus, scope: CRMScope) -> CRMRecord:
        self._require(scope, "write")
        item = self.records[crm_id]
        self._scoped(item, scope)
        if status not in TRANSITIONS[item.status]:
            raise ValueError(
                f"Invalid CRM transition: {item.status.value} -> {status.value}"
            )
        item.status, item.stage = status, status.value
        item.version += 1
        item.updated_at = utcnow()
        self.versions.append(item.to_dict())
        self._record(crm_id, scope, f"crm.transition.{status.value}")
        self._update_conversion_rate(scope)
        return item

    def add_organization(self, item: Organization, scope: CRMScope) -> Organization:
        return cast(
            Organization,
            self._add(item, self.organizations, scope, "organization.created"),
        )

    def add_contact(self, item: Contact, scope: CRMScope) -> Contact:
        validate_reference(item.public_tiktok_reference, optional=True)
        validate_reference(item.consent_reference, optional=True)
        result = cast(Contact, self._add(item, self.contacts, scope, "contact.created"))
        self.metrics.increment("tiktok_crm_contacts_total")
        return result

    def add_relationship(self, item: Relationship, scope: CRMScope) -> Relationship:
        for reference in (
            item.lead_reference,
            item.campaign_reference,
            item.creator_workspace_reference,
            item.business_workspace_reference,
        ):
            validate_reference(reference, optional=True)
            if reference:
                self.reference_port.resolve(reference, scope)
        return cast(
            Relationship,
            self._add(item, self.relationships, scope, "relationship.created"),
        )

    def add_opportunity(self, item: Opportunity, scope: CRMScope) -> Opportunity:
        if not 0 <= item.probability <= 1 or not 1 <= item.priority <= 100:
            raise ValueError("Opportunity probability or priority is out of range.")
        validate_reference(item.value_reference, optional=True)
        result = cast(
            Opportunity,
            self._add(item, self.opportunities, scope, "opportunity.created"),
        )
        self.metrics.increment("tiktok_crm_opportunities_total")
        return result

    def add_activity(self, item: Activity, scope: CRMScope) -> Activity:
        allowed = {
            "manual_note",
            "meeting_reference",
            "call_reference",
            "email_reference",
            "approved_message_reference",
            "task_reference",
            "status_change",
            "assignment_change",
        }
        if item.kind not in allowed:
            raise ValueError("Activity kind is not a CRM business record.")
        validate_reference(item.reference, optional=True)
        return cast(
            Activity, self._add(item, self.activities, scope, "activity.created")
        )

    def record_consent(self, item: ConsentRecord, scope: CRMScope) -> ConsentRecord:
        result = cast(
            ConsentRecord,
            self._add(item, self.consents, scope, f"consent.{item.status.value}"),
        )
        if (
            item.status in {ConsentStatus.WITHDRAWN, ConsentStatus.SUPPRESSED}
            or item.suppression
        ):
            for followup in self.followups.values():
                if followup.crm_id == item.crm_id:
                    followup.status = "suppressed"
        return result

    def propose_followup(self, item: FollowUp, scope: CRMScope) -> FollowUp:
        self._require(scope, "write")
        self._scoped(item, scope)
        consent = self._current_consent(item.crm_id, scope)
        if (
            not item.consent_validated
            or consent is None
            or consent.status is not ConsentStatus.GRANTED
        ):
            raise PermissionError(
                "Current granted consent is required for follow-up proposals."
            )
        if item.approval_required and not item.approved:
            item.status = "awaiting_approval"
        self.followups[item.id] = item
        self.metrics.increment("tiktok_crm_followups_total")
        self._record(item.crm_id, scope, "followup.proposed")
        return item

    def handoff_followup(self, followup_id: str, scope: CRMScope) -> str:
        self._require(scope, "handoff")
        item = self.followups[followup_id]
        self._scoped(item, scope)
        consent = self._current_consent(item.crm_id, scope)
        if item.approval_required and not item.approved:
            raise PermissionError("Approved follow-up required.")
        if (
            consent is None
            or consent.status is not ConsentStatus.GRANTED
            or consent.suppression
        ):
            raise PermissionError("Current unsuppressed consent is required.")
        receipt = self.workflow_port.propose(f"ref://crm-followup/{item.id}", scope)
        item.status = "handed_off"
        self._record(item.crm_id, scope, "followup.workflow_handoff")
        return receipt

    def _add(
        self,
        item: Any,
        collection: dict[str, Any],
        scope: CRMScope,
        action: str,
    ) -> Any:
        self._require(scope, "write")
        self._scoped(item, scope)
        if item.id in collection:
            raise ValueError("Record ID must be unique.")
        if getattr(item, "crm_id", None):
            record = self.records[item.crm_id]
            self._scoped(record, scope)
        collection[item.id] = item
        self._record(getattr(item, "crm_id", item.id), scope, action)
        return item

    def _current_consent(self, crm_id: str, scope: CRMScope) -> ConsentRecord | None:
        matches = [
            item
            for item in self.consents.values()
            if item.crm_id == crm_id
            and item.tenant == scope.tenant
            and item.workspace == scope.workspace
        ]
        return matches[-1] if matches else None

    def _update_conversion_rate(self, scope: CRMScope) -> None:
        records = self.scoped_values(self.records.values(), scope)
        won = sum(item.status is CRMStatus.WON for item in records)
        self.metrics.set(
            "tiktok_crm_conversion_rate", won / len(records) if records else 0.0
        )

    def history(self, scope: CRMScope) -> list[dict[str, Any]]:
        self._require(scope, "read")
        return [
            asdict(item)
            for item in self.audit
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def analytics(self, scope: CRMScope) -> dict[str, Any]:
        self._require(scope, "read")
        records = self.scoped_values(self.records.values(), scope)
        return {
            "crm_records": len(records),
            "organizations": len(
                self.scoped_values(self.organizations.values(), scope)
            ),
            "contacts": len(self.scoped_values(self.contacts.values(), scope)),
            "opportunities": len(
                self.scoped_values(self.opportunities.values(), scope)
            ),
            "activities": len(self.scoped_values(self.activities.values(), scope)),
            "followups": len(self.scoped_values(self.followups.values(), scope)),
            "conversions": sum(item.status is CRMStatus.WON for item in records),
            "conversion_rate": self.metrics.values["tiktok_crm_conversion_rate"],
        }

    def dashboard(self, scope: CRMScope) -> dict[str, Any]:
        return {
            "overview": self.analytics(scope),
            "organizations": [
                asdict(item)
                for item in self.scoped_values(self.organizations.values(), scope)
            ],
            "contacts": [
                asdict(item)
                for item in self.scoped_values(self.contacts.values(), scope)
            ],
            "relationships": [
                asdict(item)
                for item in self.scoped_values(self.relationships.values(), scope)
            ],
            "opportunities": [
                asdict(item)
                for item in self.scoped_values(self.opportunities.values(), scope)
            ],
            "activities": [
                asdict(item)
                for item in self.scoped_values(self.activities.values(), scope)
            ],
            "followups": [
                asdict(item)
                for item in self.scoped_values(self.followups.values(), scope)
            ],
            "history": self.history(scope),
            "outreach_execution": False,
        }
