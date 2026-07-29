"""Consent-aware, bounded lead management orchestration."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from time import perf_counter
from typing import Any

from .adapters import BoundedTestDouble, HandoffPort
from .metrics import LeadMetrics
from .models import (
    Activity,
    Assignment,
    AuditEvent,
    ConsentRecord,
    ConsentStatus,
    FollowUp,
    Handoff,
    Lead,
    LeadScope,
    LeadScore,
    LeadSource,
    LeadStatus,
    Qualification,
    utcnow,
    validate_metadata,
    validate_reference,
)

MAX_IMPORT_ROWS = 1000
ALLOWED_IMPORT_FIELDS = frozenset(
    {
        "id",
        "display_name",
        "tiktok_public_reference",
        "external_reference",
        "source_reference",
        "owner",
        "priority",
    }
)
TRANSITIONS: dict[LeadStatus, frozenset[LeadStatus]] = {
    LeadStatus.NEW: frozenset(
        {LeadStatus.VALIDATED, LeadStatus.PAUSED, LeadStatus.ARCHIVED}
    ),
    LeadStatus.IMPORTED: frozenset(
        {LeadStatus.VALIDATED, LeadStatus.DUPLICATE_REVIEW, LeadStatus.ARCHIVED}
    ),
    LeadStatus.VALIDATED: frozenset(
        {
            LeadStatus.DUPLICATE_REVIEW,
            LeadStatus.QUALIFIED,
            LeadStatus.UNQUALIFIED,
            LeadStatus.PAUSED,
        }
    ),
    LeadStatus.DUPLICATE_REVIEW: frozenset({LeadStatus.VALIDATED, LeadStatus.ARCHIVED}),
    LeadStatus.QUALIFIED: frozenset(
        {LeadStatus.ASSIGNED, LeadStatus.PAUSED, LeadStatus.ARCHIVED}
    ),
    LeadStatus.UNQUALIFIED: frozenset({LeadStatus.PAUSED, LeadStatus.ARCHIVED}),
    LeadStatus.ASSIGNED: frozenset(
        {LeadStatus.FOLLOW_UP_PLANNED, LeadStatus.PAUSED, LeadStatus.ARCHIVED}
    ),
    LeadStatus.FOLLOW_UP_PLANNED: frozenset(
        {LeadStatus.ENGAGED, LeadStatus.PAUSED, LeadStatus.ARCHIVED}
    ),
    LeadStatus.ENGAGED: frozenset(
        {LeadStatus.CONVERTED, LeadStatus.PAUSED, LeadStatus.ARCHIVED}
    ),
    LeadStatus.CONVERTED: frozenset({LeadStatus.ARCHIVED}),
    LeadStatus.PAUSED: frozenset(
        {
            LeadStatus.VALIDATED,
            LeadStatus.QUALIFIED,
            LeadStatus.ASSIGNED,
            LeadStatus.ARCHIVED,
        }
    ),
    LeadStatus.ARCHIVED: frozenset({LeadStatus.DELETED}),
    LeadStatus.DELETED: frozenset(),
}


class TikTokLeadManagementCenter:
    def __init__(self, handoffs: HandoffPort | None = None) -> None:
        self.handoff_port = handoffs or BoundedTestDouble()
        self.leads: dict[str, Lead] = {}
        self.sources: dict[str, dict[str, Any]] = {}
        self.imports: dict[str, dict[str, Any]] = {}
        self.duplicates: dict[str, dict[str, Any]] = {}
        self.qualifications: dict[str, Qualification] = {}
        self.scores: dict[str, LeadScore] = {}
        self.segments: dict[str, dict[str, Any]] = {}
        self.assignments: dict[str, Assignment] = {}
        self.consents: dict[str, ConsentRecord] = {}
        self.activities: dict[str, Activity] = {}
        self.followups: dict[str, FollowUp] = {}
        self.handoffs: dict[str, Handoff] = {}
        self.audit: list[AuditEvent] = []
        self.versions: list[dict[str, Any]] = []
        self.metrics = LeadMetrics()

    @staticmethod
    def _require(scope: LeadScope, action: str) -> None:
        permission = f"tiktok:leads:{action}"
        if (
            permission not in scope.permissions
            and "tiktok:leads:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(item: Any, scope: LeadScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def scoped_values(self, values: Any, scope: LeadScope) -> list[Any]:
        self._require(scope, "read")
        return [
            item
            for item in values
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def _record(
        self, lead: Lead, scope: LeadScope, action: str, detail: str = ""
    ) -> None:
        if any(
            secret in detail.casefold() for secret in ("token=", "cookie=", "secret=")
        ):
            raise ValueError("Secrets are forbidden in audit events.")
        self.audit.append(
            AuditEvent(
                lead.id, lead.tenant, lead.workspace, scope.actor, action, detail
            )
        )

    def create_lead(self, lead: Lead, scope: LeadScope) -> Lead:
        self._require(scope, "write")
        self._scoped(lead, scope)
        lead.validate()
        if lead.id in self.leads:
            raise ValueError("Lead ID must be unique.")
        self.leads[lead.id] = lead
        self.sources[lead.id] = {
            "tenant": lead.tenant,
            "workspace": lead.workspace,
            "source": lead.source.value,
            "reference": lead.source_reference,
            "created_at": utcnow(),
        }
        self.versions.append(lead.to_dict())
        self.metrics.increment("tiktok_leads_total")
        if lead.status is LeadStatus.NEW:
            self.metrics.increment("tiktok_leads_new_total")
        self._record(lead, scope, "lead.created")
        return lead

    def update_lead(
        self, lead_id: str, changes: dict[str, Any], scope: LeadScope
    ) -> Lead:
        self._require(scope, "write")
        lead = self.leads[lead_id]
        self._scoped(lead, scope)
        immutable = {"id", "tenant", "workspace", "source", "source_reference"}
        if immutable & changes.keys():
            raise ValueError("Lead identity, scope, and source are immutable.")
        if "metadata" in changes:
            validate_metadata(changes["metadata"])
        for key, value in changes.items():
            if not hasattr(lead, key):
                raise ValueError(f"Unknown lead field: {key}")
            setattr(lead, key, value)
        lead.version += 1
        lead.updated_at = utcnow()
        lead.validate()
        self.versions.append(lead.to_dict())
        self._record(lead, scope, "lead.updated")
        return lead

    def transition(self, lead_id: str, status: LeadStatus, scope: LeadScope) -> Lead:
        self._require(scope, "write")
        lead = self.leads[lead_id]
        self._scoped(lead, scope)
        if status not in TRANSITIONS[lead.status]:
            raise ValueError(
                f"Invalid lead transition: {lead.status.value} -> {status.value}"
            )
        lead.status = status
        lead.stage = status.value
        lead.version += 1
        lead.updated_at = utcnow()
        self.versions.append(lead.to_dict())
        if status is LeadStatus.CONVERTED:
            self.metrics.increment("tiktok_leads_converted_total")
        self._record(lead, scope, f"lead.transition.{status.value}")
        return lead

    def preview_import(
        self,
        payload: str,
        format: str,
        mapping: dict[str, str],
        scope: LeadScope,
        *,
        maximum_rows: int = MAX_IMPORT_ROWS,
    ) -> dict[str, Any]:
        self._require(scope, "import")
        if maximum_rows < 1 or maximum_rows > MAX_IMPORT_ROWS:
            raise ValueError(f"Import limit must be within [1, {MAX_IMPORT_ROWS}].")
        if format == "csv":
            rows = list(csv.DictReader(io.StringIO(payload)))
        elif format == "json":
            parsed = json.loads(payload)
            if not isinstance(parsed, list) or not all(
                isinstance(row, dict) for row in parsed
            ):
                raise ValueError("JSON import must be an array of objects.")
            rows = parsed
        else:
            raise ValueError("Only CSV and JSON imports are supported.")
        if len(rows) > maximum_rows:
            raise ValueError("Import exceeds the configured maximum row limit.")
        mapped: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        for number, row in enumerate(rows, 1):
            item = {target: row.get(source, "") for source, target in mapping.items()}
            unknown = set(item) - ALLOWED_IMPORT_FIELDS
            if unknown:
                errors.append(
                    {"row": number, "error": f"unsupported fields: {sorted(unknown)}"}
                )
            elif not item.get("id") or not item.get("display_name"):
                errors.append(
                    {"row": number, "error": "id and display_name are required"}
                )
            else:
                mapped.append(item)
        return {
            "dry_run": True,
            "row_count": len(rows),
            "valid_rows": len(mapped),
            "rows": mapped[:100],
            "errors": errors,
            "duplicates": [self.find_duplicates_from_row(row, scope) for row in mapped],
        }

    def import_records(
        self,
        import_id: str,
        payload: str,
        format: str,
        mapping: dict[str, str],
        scope: LeadScope,
        *,
        dry_run: bool = True,
        maximum_rows: int = MAX_IMPORT_ROWS,
    ) -> dict[str, Any]:
        preview = self.preview_import(
            payload, format, mapping, scope, maximum_rows=maximum_rows
        )
        record = {
            "id": import_id,
            "tenant": scope.tenant,
            "workspace": scope.workspace,
            **preview,
            "format": format,
            "maximum_rows": maximum_rows,
            "created_at": utcnow(),
        }
        if not dry_run and preview["errors"]:
            raise ValueError("Import validation failed; inspect the error report.")
        if not dry_run:
            for row in preview["rows"]:
                lead = Lead(
                    id=str(row["id"]),
                    display_name=str(row["display_name"]),
                    tenant=scope.tenant,
                    workspace=scope.workspace,
                    owner=str(row.get("owner") or scope.actor),
                    source=LeadSource.APPROVED_IMPORT,
                    source_reference=str(
                        row.get("source_reference") or f"ref://import/{import_id}"
                    ),
                    tiktok_public_reference=str(row.get("tiktok_public_reference", "")),
                    external_reference=str(row.get("external_reference", "")),
                    status=LeadStatus.IMPORTED,
                    priority=int(row.get("priority") or 50),
                )
                self.create_lead(lead, scope)
            record["dry_run"] = False
            self.metrics.increment("tiktok_leads_imports_total")
        self.imports[import_id] = record
        return record

    @staticmethod
    def _normalized_name(value: str) -> str:
        return " ".join(value.casefold().split())

    def find_duplicates_from_row(
        self, row: dict[str, Any], scope: LeadScope
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        name = self._normalized_name(str(row.get("display_name", "")))
        for lead in self.leads.values():
            if lead.tenant != scope.tenant or lead.workspace != scope.workspace:
                continue
            reasons: list[str] = []
            confidence = 0.0
            if (
                row.get("tiktok_public_reference")
                and row["tiktok_public_reference"] == lead.tiktok_public_reference
            ):
                reasons.append("exact_tiktok_public_reference")
                confidence = 1.0
            if (
                row.get("external_reference")
                and row["external_reference"] == lead.external_reference
            ):
                reasons.append("exact_external_reference")
                confidence = 1.0
            ratio = SequenceMatcher(
                None, name, self._normalized_name(lead.display_name)
            ).ratio()
            if ratio >= 0.85:
                reasons.append("bounded_fuzzy_display_name")
                confidence = max(confidence, min(ratio, 0.95))
            if reasons:
                candidates.append(
                    {"lead_id": lead.id, "confidence": confidence, "reasons": reasons}
                )
        return candidates

    def propose_merge(
        self, primary_id: str, duplicate_id: str, scope: LeadScope
    ) -> dict[str, Any]:
        self._require(scope, "review")
        primary, duplicate = self.leads[primary_id], self.leads[duplicate_id]
        self._scoped(primary, scope)
        self._scoped(duplicate, scope)
        proposal_id = f"merge-{primary_id}-{duplicate_id}"
        proposal = {
            "id": proposal_id,
            "tenant": scope.tenant,
            "workspace": scope.workspace,
            "primary_id": primary_id,
            "duplicate_id": duplicate_id,
            "status": "manual_review_required",
            "automatic_merge": False,
        }
        self.duplicates[proposal_id] = proposal
        self.metrics.increment("tiktok_leads_duplicates_total")
        return proposal

    def qualify(self, item: Qualification, scope: LeadScope) -> Qualification:
        started = perf_counter()
        self._require(scope, "qualify")
        self._scoped(item, scope)
        lead = self.leads[item.lead_id]
        self._scoped(lead, scope)
        if not item.reason or not all(
            0 <= value <= 1
            for value in (
                item.business_relevance,
                item.campaign_relevance,
                item.geographic_relevance,
                item.language_relevance,
            )
        ):
            raise ValueError(
                "Qualification requires a reason and bounded relevance values."
            )
        for reference in item.evidence_references:
            validate_reference(reference)
        self.qualifications[item.id] = item
        lead.status = LeadStatus.QUALIFIED if item.qualified else LeadStatus.UNQUALIFIED
        metric = (
            "tiktok_leads_qualified_total"
            if item.qualified
            else "tiktok_leads_unqualified_total"
        )
        self.metrics.increment(metric)
        self.metrics.set("tiktok_lead_qualification_seconds", perf_counter() - started)
        self._record(
            lead, scope, "lead.qualified" if item.qualified else "lead.unqualified"
        )
        return item

    def score(
        self,
        lead_id: str,
        scope: LeadScope,
        *,
        business_fit: float,
        engagement_reference: float,
        recency: float,
        source_quality: float,
        risk_flags: list[str] | None = None,
    ) -> LeadScore:
        self._require(scope, "score")
        lead = self.leads[lead_id]
        self._scoped(lead, scope)
        factors = [business_fit, engagement_reference, recency, source_quality]
        if not all(0 <= value <= 1 for value in factors):
            raise ValueError("Scoring factors must be within [0, 1].")
        consent = (
            1.0
            if lead.consent_status
            in {ConsentStatus.GRANTED, ConsentStatus.NOT_REQUIRED}
            else 0.0
        )
        risks = list(risk_flags or [])
        raw = sum((*factors, consent)) / 5
        penalty = min(0.5, len(risks) * 0.1)
        score = round(max(0.0, raw - penalty) * 100, 2)
        result = LeadScore(
            id=f"score-{lead_id}-{lead.version}",
            lead_id=lead_id,
            tenant=lead.tenant,
            workspace=lead.workspace,
            score=score,
            priority=max(1, min(100, round(score))),
            confidence=0.8,
            business_fit=business_fit,
            engagement_reference=engagement_reference,
            recency=recency,
            source_quality=source_quality,
            consent_state=consent,
            risk_flags=risks,
            explanation=[
                "Equal bounded weights: business fit, engagement reference, "
                "recency, source quality, consent state.",
                f"Risk penalty={penalty:.2f}; no protected attributes are used.",
            ],
        )
        self.scores[result.id] = result
        return result

    def add_segment(
        self, segment_id: str, kind: str, lead_ids: list[str], scope: LeadScope
    ) -> dict[str, Any]:
        self._require(scope, "write")
        allowed = {
            "campaign",
            "product",
            "region",
            "language",
            "interest",
            "status",
            "priority",
            "custom",
        }
        if kind not in allowed or len(lead_ids) > 1000:
            raise ValueError("Segment kind or size is outside bounded limits.")
        for lead_id in lead_ids:
            self._scoped(self.leads[lead_id], scope)
        result = {
            "id": segment_id,
            "tenant": scope.tenant,
            "workspace": scope.workspace,
            "kind": kind,
            "lead_ids": list(dict.fromkeys(lead_ids)),
        }
        self.segments[segment_id] = result
        return result

    def assign(self, item: Assignment, scope: LeadScope) -> Assignment:
        started = perf_counter()
        self._require(scope, "assign")
        self._scoped(item, scope)
        lead = self.leads[item.lead_id]
        self._scoped(lead, scope)
        if item.capacity < 1 or not 1 <= item.priority <= 100:
            raise ValueError("Assignment capacity or priority is invalid.")
        validate_reference(item.rule_reference)
        self.assignments[item.id] = item
        lead.owner = item.owner
        lead.status = LeadStatus.ASSIGNED
        self.metrics.increment("tiktok_leads_assigned_total")
        self.metrics.set("tiktok_lead_assignment_seconds", perf_counter() - started)
        self._record(lead, scope, "assignment.changed", item.owner)
        return item

    def record_consent(self, item: ConsentRecord, scope: LeadScope) -> ConsentRecord:
        self._require(scope, "consent")
        self._scoped(item, scope)
        lead = self.leads[item.lead_id]
        self._scoped(lead, scope)
        if not item.source or not item.purpose:
            raise ValueError("Consent source and purpose are required.")
        if (
            item.status is ConsentStatus.GRANTED
            and item.expires_at
            and item.expires_at <= datetime.now(timezone.utc)
        ):
            raise ValueError("Granted consent cannot already be expired.")
        if item.status is ConsentStatus.WITHDRAWN:
            item.suppression = True
            self.metrics.increment("tiktok_leads_consent_withdrawals_total")
        lead.consent_status = (
            ConsentStatus.SUPPRESSED if item.suppression else item.status
        )
        self.consents[item.id] = item
        self._record(lead, scope, "consent.changed", lead.consent_status.value)
        return item

    def add_activity(self, item: Activity, scope: LeadScope) -> Activity:
        self._require(scope, "write")
        self._scoped(item, scope)
        self._scoped(self.leads[item.lead_id], scope)
        allowed = {
            "manual_note",
            "call_reference",
            "email_reference",
            "approved_message_reference",
            "meeting_reference",
            "campaign_activity_reference",
            "interaction_reference",
            "status_change",
            "assignment_change",
            "consent_change",
            "audit",
        }
        if item.kind not in allowed:
            raise ValueError("Unsupported activity kind.")
        validate_reference(item.reference, optional=item.kind == "manual_note")
        self.activities[item.id] = item
        return item

    def plan_followup(self, item: FollowUp, scope: LeadScope) -> FollowUp:
        self._require(scope, "followup")
        self._scoped(item, scope)
        lead = self.leads[item.lead_id]
        self._scoped(lead, scope)
        if lead.consent_status not in {
            ConsentStatus.GRANTED,
            ConsentStatus.NOT_REQUIRED,
        }:
            raise PermissionError("Consent or documented lawful basis is required.")
        if any(c.lead_id == lead.id and c.suppression for c in self.consents.values()):
            raise PermissionError("Suppression blocks follow-up proposals.")
        validate_reference(item.channel_reference)
        validate_reference(item.template_reference)
        if not 1 <= item.priority <= 100:
            raise ValueError("Follow-up priority must be within [1, 100].")
        item.status = "approved_manual_task" if item.approved else "proposed"
        self.followups[item.id] = item
        lead.status = LeadStatus.FOLLOW_UP_PLANNED
        if item.due_at <= datetime.now(timezone.utc):
            self.metrics.increment("tiktok_leads_followups_due_total")
        self._record(lead, scope, "followup.proposed")
        return item

    def handoff(self, item: Handoff, scope: LeadScope) -> Handoff:
        self._require(scope, "handoff")
        self._scoped(item, scope)
        lead = self.leads[item.lead_id]
        self._scoped(lead, scope)
        if not item.approved:
            raise PermissionError("Handoff requires explicit approval.")
        if lead.status is LeadStatus.PAUSED:
            raise PermissionError("Workspace or lead pause blocks handoff.")
        validate_reference(item.reference)
        item.receipt_reference = self.handoff_port.propose(
            item.target, item.reference, scope
        )
        validate_reference(item.receipt_reference)
        self.handoffs[item.id] = item
        self._record(lead, scope, "handoff.proposed", item.target.value)
        return item

    def analytics(self, scope: LeadScope) -> dict[str, Any]:
        leads = self.scoped_values(self.leads.values(), scope)
        by_source: dict[str, int] = {}
        by_stage: dict[str, int] = {}
        by_consent: dict[str, int] = {}
        for lead in leads:
            by_source[lead.source.value] = by_source.get(lead.source.value, 0) + 1
            by_stage[lead.stage] = by_stage.get(lead.stage, 0) + 1
            by_consent[lead.consent_status.value] = (
                by_consent.get(lead.consent_status.value, 0) + 1
            )
        qualified = sum(lead.status is LeadStatus.QUALIFIED for lead in leads)
        converted = sum(lead.status is LeadStatus.CONVERTED for lead in leads)
        return {
            "leads_total": len(leads),
            "new_leads": sum(lead.status is LeadStatus.NEW for lead in leads),
            "qualified_leads": qualified,
            "unqualified_leads": sum(
                lead.status is LeadStatus.UNQUALIFIED for lead in leads
            ),
            "assigned_leads": sum(lead.status is LeadStatus.ASSIGNED for lead in leads),
            "followups_due": sum(
                item.due_at <= datetime.now(timezone.utc)
                for item in self.scoped_values(self.followups.values(), scope)
            ),
            "converted_leads": converted,
            "archived_leads": sum(lead.status is LeadStatus.ARCHIVED for lead in leads),
            "source_distribution": by_source,
            "stage_distribution": by_stage,
            "score_distribution": [
                item.score for item in self.scoped_values(self.scores.values(), scope)
            ],
            "consent_distribution": by_consent,
            "qualification_rate": qualified / len(leads) if leads else 0.0,
            "conversion_reference_rate": converted / len(leads) if leads else 0.0,
            "average_qualification_time": self.metrics.values[
                "tiktok_lead_qualification_seconds"
            ],
            "average_assignment_time": self.metrics.values[
                "tiktok_lead_assignment_seconds"
            ],
        }

    def history(self, scope: LeadScope) -> dict[str, Any]:
        def scoped(values: Any) -> list[dict[str, Any]]:
            return [asdict(item) for item in self.scoped_values(values, scope)]

        return {
            "lead_history": [
                item
                for item in self.versions
                if item["tenant"] == scope.tenant
                and item["workspace"] == scope.workspace
            ],
            "source_history": [
                item
                for item in self.sources.values()
                if item["tenant"] == scope.tenant
                and item["workspace"] == scope.workspace
            ],
            "import_history": [
                item
                for item in self.imports.values()
                if item["tenant"] == scope.tenant
                and item["workspace"] == scope.workspace
            ],
            "qualification_history": scoped(self.qualifications.values()),
            "score_history": scoped(self.scores.values()),
            "assignment_history": scoped(self.assignments.values()),
            "consent_history": scoped(self.consents.values()),
            "activity_history": scoped(self.activities.values()),
            "followup_history": scoped(self.followups.values()),
            "handoff_history": scoped(self.handoffs.values()),
            "audit_trail": scoped(self.audit),
        }

    def dashboard(self, scope: LeadScope) -> dict[str, Any]:
        return {
            "sections": [
                "Lead Overview",
                "Leads",
                "Sources",
                "Imports",
                "Duplicates",
                "Qualification",
                "Scoring",
                "Segments",
                "Assignments",
                "Consent",
                "Activities",
                "Follow-Ups",
                "Handoffs",
                "History",
                "Analytics",
            ],
            "lead_overview": self.analytics(scope),
            "safety": {
                "direct_outreach_execution": False,
                "bulk_messaging": False,
                "private_data_scraping": False,
                "consent_aware_proposals": True,
                "approval_gated_handoffs": True,
            },
        }
