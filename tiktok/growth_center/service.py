"""Advisory-only TikTok growth analysis, planning, and tracking."""

from __future__ import annotations

from dataclasses import asdict
from time import perf_counter
from typing import Any

from .adapters import BoundedTestDouble, ProposalPort, ReadOnlyGrowthInputPort
from .metrics import GrowthMetrics
from .models import (
    Approval,
    AuditEvent,
    GrowthGoal,
    GrowthOpportunity,
    GrowthProfile,
    GrowthRecommendation,
    GrowthSimulation,
    GrowthStatus,
    KPIRecord,
    RequestScope,
    SimulationKind,
    TrendRecord,
    utcnow,
    validate_reference,
)

TRANSITIONS: dict[GrowthStatus, frozenset[GrowthStatus]] = {
    GrowthStatus.DRAFT: frozenset({GrowthStatus.ANALYZING, GrowthStatus.ARCHIVED}),
    GrowthStatus.ANALYZING: frozenset({GrowthStatus.PROPOSED}),
    GrowthStatus.PROPOSED: frozenset({GrowthStatus.REVIEW, GrowthStatus.ARCHIVED}),
    GrowthStatus.REVIEW: frozenset({GrowthStatus.APPROVED, GrowthStatus.PROPOSED}),
    GrowthStatus.APPROVED: frozenset({GrowthStatus.TRACKING, GrowthStatus.ARCHIVED}),
    GrowthStatus.TRACKING: frozenset({GrowthStatus.COMPLETED}),
    GrowthStatus.COMPLETED: frozenset({GrowthStatus.ARCHIVED}),
    GrowthStatus.ARCHIVED: frozenset({GrowthStatus.DELETED}),
    GrowthStatus.DELETED: frozenset(),
}


class TikTokAIGrowthCenter:
    """Generates bounded recommendations and approved proposal references."""

    def __init__(
        self,
        inputs: ReadOnlyGrowthInputPort | None = None,
        proposals: ProposalPort | None = None,
    ) -> None:
        adapter = BoundedTestDouble()
        self.input_port = inputs or adapter
        self.proposal_port = proposals or adapter
        self.profiles: dict[str, GrowthProfile] = {}
        self.goals: dict[str, GrowthGoal] = {}
        self.kpis: dict[str, KPIRecord] = {}
        self.trends: dict[str, TrendRecord] = {}
        self.recommendations: dict[str, GrowthRecommendation] = {}
        self.opportunities: dict[str, GrowthOpportunity] = {}
        self.simulations: dict[str, GrowthSimulation] = {}
        self.approvals: dict[str, Approval] = {}
        self.audit: list[AuditEvent] = []
        self.profile_versions: list[dict[str, Any]] = []
        self.metrics = GrowthMetrics()

    @staticmethod
    def _require(scope: RequestScope, action: str) -> None:
        permission = f"tiktok:growth:{action}"
        if (
            permission not in scope.permissions
            and "tiktok:growth:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(item: Any, scope: RequestScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def scoped_values(self, values: Any, scope: RequestScope) -> list[Any]:
        self._require(scope, "read")
        return [
            item
            for item in values
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def _record(
        self, profile: GrowthProfile, scope: RequestScope, action: str, detail: str = ""
    ) -> None:
        if any(
            marker in detail.casefold()
            for marker in ("password=", "secret=", "token=", "cookie=")
        ):
            raise ValueError("Secrets are forbidden in growth audit records.")
        self.audit.append(
            AuditEvent(
                profile.id,
                profile.tenant,
                profile.workspace,
                scope.actor,
                action,
                detail,
            )
        )

    def create_profile(
        self, profile: GrowthProfile, scope: RequestScope
    ) -> GrowthProfile:
        self._require(scope, "write")
        self._scoped(profile, scope)
        profile.validate()
        if profile.id in self.profiles:
            raise ValueError("Growth profile ID must be unique.")
        self.profiles[profile.id] = profile
        self.profile_versions.append(profile.to_dict())
        self.metrics.increment("tiktok_growth_profiles_total")
        self._record(profile, scope, "profile.created")
        return profile

    def transition(
        self, profile_id: str, status: GrowthStatus, scope: RequestScope
    ) -> GrowthProfile:
        self._require(scope, "write")
        profile = self.profiles[profile_id]
        self._scoped(profile, scope)
        if status not in TRANSITIONS[profile.status]:
            raise ValueError(
                f"Invalid growth transition: {profile.status.value} -> {status.value}"
            )
        profile.status = status
        profile.version += 1
        profile.updated_at = utcnow()
        self.profile_versions.append(profile.to_dict())
        self._record(profile, scope, f"profile.transition.{status.value}")
        return profile

    def add_goal(self, goal: GrowthGoal, scope: RequestScope) -> GrowthGoal:
        self._require(scope, "write")
        self._scoped(goal, scope)
        if goal.kind.value == "custom_bounded_goal" and not goal.bounded_definition:
            raise ValueError("Custom goals require a bounded definition.")
        self.goals[goal.id] = goal
        self.metrics.increment("tiktok_growth_goals_total")
        return goal

    def record_kpi(self, kpi: KPIRecord, scope: RequestScope) -> KPIRecord:
        self._require(scope, "analyze")
        self._scoped(kpi, scope)
        validate_reference(kpi.source_reference)
        self.kpis[kpi.id] = kpi
        return kpi

    def analyze_trend(self, trend: TrendRecord, scope: RequestScope) -> TrendRecord:
        self._require(scope, "analyze")
        self._scoped(trend, scope)
        if not trend.source_references:
            raise ValueError("Trend analysis requires read-only evidence references.")
        for reference in trend.source_references:
            validate_reference(reference)
        self.trends[trend.id] = trend
        self.metrics.increment("tiktok_growth_trends_total")
        return trend

    def recommend(
        self, recommendation: GrowthRecommendation, scope: RequestScope
    ) -> GrowthRecommendation:
        started = perf_counter()
        self._require(scope, "analyze")
        self._scoped(recommendation, scope)
        if recommendation.approved or recommendation.proposal_reference:
            raise ValueError("Recommendations must be advisory when created.")
        if not 0 <= recommendation.confidence <= 1:
            raise ValueError("Confidence must be within [0, 1].")
        if not recommendation.evidence_references:
            raise ValueError("Recommendations require evidence references.")
        for reference in recommendation.evidence_references:
            validate_reference(reference)
        unsafe = (
            "captcha",
            "bypass",
            "circumvent",
            "anti-detection",
            "spam",
            "mass action",
        )
        text = f"{recommendation.title} {recommendation.rationale}".casefold()
        if any(term in text for term in unsafe):
            raise ValueError("Unsafe growth recommendations are forbidden.")
        self.recommendations[recommendation.id] = recommendation
        self.metrics.increment("tiktok_growth_recommendations_total")
        self.metrics.set("tiktok_growth_latency_seconds", perf_counter() - started)
        return recommendation

    def add_opportunity(
        self, opportunity: GrowthOpportunity, scope: RequestScope
    ) -> GrowthOpportunity:
        self._require(scope, "analyze")
        self._scoped(opportunity, scope)
        if (
            not 0 <= opportunity.impact_score <= 1
            or not 0 <= opportunity.effort_score <= 1
        ):
            raise ValueError("Opportunity scores must be within [0, 1].")
        self.opportunities[opportunity.id] = opportunity
        return opportunity

    def simulate(
        self, simulation: GrowthSimulation, scope: RequestScope
    ) -> GrowthSimulation:
        self._require(scope, "analyze")
        self._scoped(simulation, scope)
        if simulation.live_dependency:
            raise ValueError("Growth simulations cannot depend on live TikTok.")
        if not 0 <= simulation.confidence <= 1:
            raise ValueError("Confidence must be within [0, 1].")
        validate_reference(simulation.result_reference)
        self.simulations[simulation.id] = simulation
        if simulation.kind in {
            SimulationKind.FORECAST,
            SimulationKind.GROWTH_PROJECTION,
        }:
            self.metrics.increment("tiktok_growth_forecasts_total")
        return simulation

    def approve(self, approval: Approval, scope: RequestScope) -> Approval:
        self._require(scope, "approve")
        self._scoped(approval, scope)
        recommendation = self.recommendations[approval.recommendation_id]
        self._scoped(recommendation, scope)
        if not approval.approved and not approval.notes:
            raise ValueError("Rejected recommendations require notes.")
        recommendation.approved = approval.approved
        self.approvals[approval.id] = approval
        return approval

    def create_execution_proposal(
        self, recommendation_id: str, scope: RequestScope
    ) -> str:
        self._require(scope, "propose")
        recommendation = self.recommendations[recommendation_id]
        self._scoped(recommendation, scope)
        approved = any(
            item.recommendation_id == recommendation_id and item.approved
            for item in self.scoped_values(self.approvals.values(), scope)
        )
        if not recommendation.approved or not approved:
            raise PermissionError(
                "Human approval is required before creating a proposal."
            )
        recommendation.proposal_reference = self.proposal_port.propose(
            recommendation_id, scope
        )
        validate_reference(recommendation.proposal_reference)
        return recommendation.proposal_reference

    def integration_snapshot(self, scope: RequestScope) -> dict[str, dict[str, Any]]:
        self._require(scope, "analyze")
        from .adapters import INTEGRATION_MODULES

        return {
            module: self.input_port.snapshot(module, scope)
            for module in INTEGRATION_MODULES
        }

    def analytics(self, scope: RequestScope) -> dict[str, float]:
        recommendations = self.scoped_values(self.recommendations.values(), scope)
        goals = self.scoped_values(self.goals.values(), scope)
        kpis = self.scoped_values(self.kpis.values(), scope)
        return {
            "growth_profiles": float(
                len(self.scoped_values(self.profiles.values(), scope))
            ),
            "active_goals": float(len(goals)),
            "kpis_tracked": float(len(kpis)),
            "recommendations": float(len(recommendations)),
            "approved_recommendations": float(
                sum(item.approved for item in recommendations)
            ),
            "average_kpi_value": sum(item.value for item in kpis) / len(kpis)
            if kpis
            else 0.0,
        }

    def dashboard(self, scope: RequestScope) -> dict[str, Any]:
        names = (
            "profiles",
            "goals",
            "kpis",
            "trends",
            "recommendations",
            "opportunities",
            "simulations",
        )
        return {
            "sections": [
                "Growth Overview",
                "Goals",
                "KPIs",
                "Trends",
                "Recommendations",
                "Opportunities",
                "Forecast",
                "Analytics",
            ],
            "growth_overview": {
                name: len(self.scoped_values(getattr(self, name).values(), scope))
                for name in names
            },
            "analytics": self.analytics(scope),
        }

    def history(self, scope: RequestScope) -> dict[str, Any]:
        return {
            "profile_versions": [
                item
                for item in self.profile_versions
                if item["tenant"] == scope.tenant
                and item["workspace"] == scope.workspace
            ],
            "audit_trail": [
                asdict(item) for item in self.scoped_values(self.audit, scope)
            ],
        }
