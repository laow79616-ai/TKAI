"""Tenant-isolated, advisory customer journey orchestration."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from time import perf_counter
from typing import Any, Protocol, TypeVar

from .adapters import HandoffPort, ReferenceOnlyHandoffAdapter
from .metrics import JourneyMetrics
from .models import (
    AuditEvent,
    ConsentState,
    Conversion,
    Handoff,
    Journey,
    JourneyScope,
    JourneyStage,
    JourneyStatus,
    Milestone,
    MilestoneState,
    Recommendation,
    Segment,
    Touchpoint,
    utcnow,
    validate_reference,
)

TRANSITIONS: dict[JourneyStatus, frozenset[JourneyStatus]] = {
    JourneyStatus.NEW: frozenset({JourneyStatus.AWARENESS, JourneyStatus.ARCHIVED}),
    JourneyStatus.AWARENESS: frozenset(
        {JourneyStatus.INTEREST, JourneyStatus.INACTIVE, JourneyStatus.ARCHIVED}
    ),
    JourneyStatus.INTEREST: frozenset(
        {JourneyStatus.CONSIDERATION, JourneyStatus.INACTIVE, JourneyStatus.ARCHIVED}
    ),
    JourneyStatus.CONSIDERATION: frozenset(
        {JourneyStatus.QUALIFIED, JourneyStatus.INACTIVE, JourneyStatus.ARCHIVED}
    ),
    JourneyStatus.QUALIFIED: frozenset(
        {JourneyStatus.OPPORTUNITY, JourneyStatus.INACTIVE, JourneyStatus.ARCHIVED}
    ),
    JourneyStatus.OPPORTUNITY: frozenset(
        {JourneyStatus.CONVERTED, JourneyStatus.INACTIVE, JourneyStatus.ARCHIVED}
    ),
    JourneyStatus.CONVERTED: frozenset({JourneyStatus.ARCHIVED}),
    JourneyStatus.INACTIVE: frozenset(
        {JourneyStatus.AWARENESS, JourneyStatus.INTEREST, JourneyStatus.ARCHIVED}
    ),
    JourneyStatus.ARCHIVED: frozenset({JourneyStatus.DELETED}),
    JourneyStatus.DELETED: frozenset(),
}

TOUCHPOINT_KINDS = frozenset(
    {
        "campaign_reference",
        "content_reference",
        "publishing_reference",
        "manual_activity",
        "approved_interaction_reference",
        "meeting_reference",
        "workflow_reference",
    }
)


class Scoped(Protocol):
    tenant: str
    workspace: str


ScopedItem = TypeVar("ScopedItem", bound=Scoped)


class TikTokCustomerJourneyCenter:
    def __init__(self, handoff_port: HandoffPort | None = None) -> None:
        self.handoff_port = handoff_port or ReferenceOnlyHandoffAdapter()
        self.metrics = JourneyMetrics()
        self.journeys: dict[str, Journey] = {}
        self.touchpoints: dict[str, Touchpoint] = {}
        self.milestones: dict[str, Milestone] = {}
        self.segments: dict[str, Segment] = {}
        self.recommendations: dict[str, Recommendation] = {}
        self.conversions: dict[str, Conversion] = {}
        self.handoffs: dict[str, Handoff] = {}
        self.versions: list[dict[str, Any]] = []
        self.audit: list[AuditEvent] = []
        self.stage_history: list[dict[str, Any]] = []

    @staticmethod
    def _require(scope: JourneyScope, action: str) -> None:
        permissions = scope.permissions
        if (
            "tiktok:customer-journeys:admin" not in permissions
            and f"tiktok:customer-journeys:{action}" not in permissions
        ):
            raise PermissionError(f"Missing customer journey {action} permission.")

    @staticmethod
    def _scoped(item: ScopedItem, scope: JourneyScope) -> ScopedItem:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Tenant or workspace isolation violation.")
        return item

    @staticmethod
    def scoped_values(values: Iterable[Any], scope: JourneyScope) -> list[Any]:
        return [
            value
            for value in values
            if value.tenant == scope.tenant and value.workspace == scope.workspace
        ]

    def _journey(self, journey_id: str, scope: JourneyScope) -> Journey:
        return self._scoped(self.journeys[journey_id], scope)

    def _record(
        self, journey: Journey, scope: JourneyScope, action: str, detail: str = ""
    ) -> None:
        self.audit.append(
            AuditEvent(
                journey.id,
                journey.tenant,
                journey.workspace,
                scope.actor,
                action,
                detail,
            )
        )

    def create_journey(self, item: Journey, scope: JourneyScope) -> Journey:
        started = perf_counter()
        self._require(scope, "write")
        self._scoped(item, scope)
        item.validate()
        if item.id in self.journeys:
            raise ValueError("Journey identifier already exists.")
        self.journeys[item.id] = item
        self.versions.append(item.to_dict())
        self.metrics.increment("tiktok_customer_journeys_total")
        self.metrics.set(
            "tiktok_customer_journey_latency_seconds", perf_counter() - started
        )
        self._record(item, scope, "journey.created")
        return item

    def transition(
        self,
        journey_id: str,
        status: JourneyStatus,
        stage: JourneyStage,
        scope: JourneyScope,
        *,
        custom_stage: str = "",
    ) -> Journey:
        started = perf_counter()
        self._require(scope, "write")
        item = self._journey(journey_id, scope)
        if status not in TRANSITIONS[item.status]:
            raise ValueError(
                f"Invalid journey transition: {item.status.value} -> {status.value}"
            )
        if stage is JourneyStage.CUSTOM and not 1 <= len(custom_stage.strip()) <= 80:
            raise ValueError("Custom stages require a bounded 1-80 character name.")
        previous = item.stage
        changed_at = utcnow()
        item.status = status
        item.stage = stage
        item.version += 1
        item.updated_at = changed_at
        self.stage_history.append(
            {
                "journey_id": item.id,
                "tenant": item.tenant,
                "workspace": item.workspace,
                "from": previous.value,
                "to": stage.value,
                "custom_stage": custom_stage,
                "timestamp": changed_at,
            }
        )
        self.versions.append(item.to_dict())
        self.metrics.set(
            "tiktok_customer_stage_latency_seconds", perf_counter() - started
        )
        self._record(item, scope, "journey.transition", stage.value)
        return item

    def add_touchpoint(self, item: Touchpoint, scope: JourneyScope) -> Touchpoint:
        self._require(scope, "write")
        self._scoped(item, scope)
        self._journey(item.journey_id, scope)
        if item.kind not in TOUCHPOINT_KINDS:
            raise ValueError("Unsupported touchpoint kind.")
        validate_reference(item.reference, optional=item.kind == "manual_activity")
        self.touchpoints[item.id] = item
        self._record(
            self.journeys[item.journey_id], scope, "touchpoint.added", item.kind
        )
        return item

    def add_milestone(self, item: Milestone, scope: JourneyScope) -> Milestone:
        self._require(scope, "write")
        self._scoped(item, scope)
        self._journey(item.journey_id, scope)
        if item.state in {MilestoneState.SKIPPED, MilestoneState.MANUAL_OVERRIDE}:
            if not item.reason.strip():
                raise ValueError("Skipped and overridden milestones require a reason.")
        self.milestones[item.id] = item
        self._record(
            self.journeys[item.journey_id], scope, "milestone.changed", item.state.value
        )
        return item

    def add_segment(self, item: Segment, scope: JourneyScope) -> Segment:
        self._require(scope, "write")
        self._scoped(item, scope)
        self._journey(item.journey_id, scope)
        if not 1 <= item.priority <= 100:
            raise ValueError("Segment priority must be within [1, 100].")
        for reference in (item.campaign,):
            validate_reference(reference, optional=True)
        self.segments[item.id] = item
        return item

    def recommend(
        self, item: Recommendation, scope: JourneyScope
    ) -> Recommendation:
        self._require(scope, "recommend")
        self._scoped(item, scope)
        journey = self._journey(item.journey_id, scope)
        if not item.advisory_only:
            raise ValueError("Customer journey recommendations must remain advisory.")
        if not 0 <= item.confidence <= 1 or not item.evidence:
            raise ValueError("Recommendation confidence and evidence are required.")
        for reference in (
            *item.evidence,
            item.suggested_campaign,
            item.suggested_content,
            item.suggested_workflow,
            item.suggested_follow_up_proposal,
        ):
            validate_reference(reference, optional=True)
        segment = next(
            (
                value
                for value in self.segments.values()
                if value.journey_id == journey.id
                and value.tenant == scope.tenant
                and value.workspace == scope.workspace
            ),
            None,
        )
        if segment and segment.consent_state in {
            ConsentState.WITHDRAWN,
            ConsentState.SUPPRESSED,
            ConsentState.EXPIRED,
        } and item.suggested_follow_up_proposal:
            raise PermissionError("Consent state blocks follow-up proposals.")
        self.recommendations[item.id] = item
        self._record(journey, scope, "recommendation.created")
        return item

    def record_conversion(self, item: Conversion, scope: JourneyScope) -> Conversion:
        self._require(scope, "write")
        self._scoped(item, scope)
        journey = self._journey(item.journey_id, scope)
        for reference in (item.conversion_reference, item.attribution_reference):
            validate_reference(reference)
        if not item.event.strip() or not item.outcome.strip():
            raise ValueError("Conversion event and outcome are required.")
        self.conversions[item.id] = item
        self.metrics.increment("tiktok_customer_conversions_total")
        self._record(journey, scope, "conversion.recorded", item.outcome)
        return item

    def handoff(self, item: Handoff, scope: JourneyScope) -> Handoff:
        self._require(scope, "handoff")
        self._scoped(item, scope)
        journey = self._journey(item.journey_id, scope)
        if not item.approved:
            raise PermissionError("Reference-only handoff requires explicit approval.")
        segment = next(
            (
                value
                for value in self.segments.values()
                if value.journey_id == item.journey_id
                and value.tenant == scope.tenant
                and value.workspace == scope.workspace
            ),
            None,
        )
        if segment and segment.consent_state in {
            ConsentState.WITHDRAWN,
            ConsentState.SUPPRESSED,
        }:
            raise PermissionError("Consent suppression blocks workflow handoff.")
        validate_reference(item.reference)
        item.receipt_reference = self.handoff_port.propose(
            item.target, item.reference, scope
        )
        validate_reference(item.receipt_reference)
        self.handoffs[item.id] = item
        self._record(journey, scope, "handoff.proposed", item.target.value)
        return item

    def analytics(self, scope: JourneyScope) -> dict[str, Any]:
        journeys = self.scoped_values(self.journeys.values(), scope)
        conversions = self.scoped_values(self.conversions.values(), scope)
        completed = sum(item.status is JourneyStatus.CONVERTED for item in journeys)
        dropped = sum(item.status is JourneyStatus.INACTIVE for item in journeys)
        conversion_rate = len(conversions) / len(journeys) if journeys else 0.0
        completion_rate = completed / len(journeys) if journeys else 0.0
        dropoff_rate = dropped / len(journeys) if journeys else 0.0
        durations: dict[str, list[float]] = {}
        histories = [
            item
            for item in self.stage_history
            if item["tenant"] == scope.tenant and item["workspace"] == scope.workspace
        ]
        by_journey: dict[str, list[dict[str, Any]]] = {}
        for entry in histories:
            by_journey.setdefault(str(entry["journey_id"]), []).append(entry)
        for entries in by_journey.values():
            entries.sort(key=lambda entry: entry["timestamp"])
            for current, following in zip(entries, entries[1:], strict=False):
                elapsed = following["timestamp"] - current["timestamp"]
                seconds = elapsed.total_seconds()
                durations.setdefault(str(current["to"]), []).append(seconds)
        stage_duration = {
            key: sum(values) / len(values) for key, values in durations.items()
        }
        self.metrics.set("tiktok_customer_dropoff_rate", dropoff_rate)
        self.metrics.set("tiktok_customer_completion_rate", completion_rate)
        return {
            "journey_kpis": {
                "total": len(journeys),
                "active": sum(
                    item.status
                    not in {
                        JourneyStatus.INACTIVE,
                        JourneyStatus.ARCHIVED,
                        JourneyStatus.DELETED,
                    }
                    for item in journeys
                ),
                "converted": completed,
            },
            "stage_duration_seconds": stage_duration,
            "conversion_rate": conversion_rate,
            "dropoff_rate": dropoff_rate,
            "completion_rate": completion_rate,
            "trend": [item.to_dict() for item in journeys],
            "history": histories,
        }

    def history(self, scope: JourneyScope) -> dict[str, Any]:
        def values(collection: dict[str, Any]) -> list[dict[str, Any]]:
            return [
                asdict(item)
                for item in self.scoped_values(collection.values(), scope)
            ]

        return {
            "journeys": [
                value
                for value in self.versions
                if value["tenant"] == scope.tenant
                and value["workspace"] == scope.workspace
            ],
            "stages": [
                value
                for value in self.stage_history
                if value["tenant"] == scope.tenant
                and value["workspace"] == scope.workspace
            ],
            "touchpoints": values(self.touchpoints),
            "milestones": values(self.milestones),
            "segments": values(self.segments),
            "recommendations": values(self.recommendations),
            "conversions": values(self.conversions),
            "handoffs": values(self.handoffs),
            "audit": [
                asdict(item) for item in self.scoped_values(self.audit, scope)
            ],
        }

    def dashboard(self, scope: JourneyScope) -> dict[str, Any]:
        self._require(scope, "read")
        return {
            "sections": [
                "Journey Overview",
                "Stages",
                "Touchpoints",
                "Milestones",
                "Recommendations",
                "Conversions",
                "Analytics",
                "History",
            ],
            "overview": self.analytics(scope),
            "safety": {
                "automatic_contact": False,
                "direct_outreach_execution": False,
                "platform_protection_bypass": False,
                "recommendations_advisory_only": True,
                "handoffs_reference_only": True,
                "approval_enforced": True,
                "consent_aware": True,
            },
        }
