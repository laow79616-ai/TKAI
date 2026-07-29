"""Advisory plan generation, simulation, validation, and review."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from statistics import mean
from time import perf_counter
from typing import Any, Protocol, TypeVar

from .adapters import (
    PLANNING_SOURCES,
    ReadOnlyPlanningSource,
    ReferenceOnlyPlanningSource,
)
from .metrics import PlanningMetrics
from .models import (
    Approval,
    Assumption,
    CandidatePlan,
    Evaluation,
    PlanningArtifact,
    PlanningContext,
    PlanningProfile,
    PlanningStatus,
    PlanStep,
    ReferenceHandoff,
    utcnow,
    validate_reference,
    validate_safe_mapping,
)

RESOURCE_NAMES = (
    "profiles",
    "objectives",
    "inputs",
    "constraints",
    "assumptions",
    "plans",
    "steps",
    "dependencies",
    "resources",
    "schedules",
    "risks",
    "scenarios",
    "simulations",
    "comparisons",
    "validations",
    "evaluations",
    "recommendations",
    "reviews",
    "approvals",
    "versions",
    "handoffs",
)
HANDOFF_DESTINATIONS = frozenset(
    {
        "governance_center",
        "autonomous_strategy",
        "mission_engine",
        "autonomous_operation",
        "operations_planner",
        "decision_center",
        "workflow_center",
        "task_scheduler",
        "resource_center",
        "recovery_resilience",
        "risk_control",
        "operations_center",
    }
)
SCORE_NAMES = (
    "objective_alignment",
    "constraint_compliance",
    "resource_feasibility",
    "schedule_feasibility",
    "dependency_quality",
    "risk_quality",
    "governance_readiness",
    "recovery_readiness",
    "evidence_completeness",
    "assumption_quality",
)


class IdentifiedRecord(Protocol):
    @property
    def id(self) -> str: ...


T = TypeVar("T", bound=IdentifiedRecord)


class TikTokAutonomousPlanningCenter:
    """Produces immutable, explainable plans without operational authority."""

    def __init__(
        self,
        sources: Mapping[str, ReadOnlyPlanningSource] | None = None,
        *,
        max_horizon_days: int = 365,
        max_plans: int = 100,
        max_steps_per_plan: int = 250,
        max_results: int = 500,
    ) -> None:
        if not 1 <= max_horizon_days <= 730:
            raise ValueError("Planning horizon bound is unsupported.")
        if not 1 <= max_plans <= 1_000 or not 1 <= max_steps_per_plan <= 1_000:
            raise ValueError("Plan or step bound is unsupported.")
        if not 1 <= max_results <= 1_000:
            raise ValueError("Result bound is unsupported.")
        supplied = sources or {}
        self.sources = {
            name: supplied.get(name, ReferenceOnlyPlanningSource(name))
            for name in PLANNING_SOURCES
        }
        self.max_horizon_days = max_horizon_days
        self.max_plans = max_plans
        self.max_steps_per_plan = max_steps_per_plan
        self.max_results = max_results
        self.profiles: dict[str, PlanningProfile] = {}
        self.objectives: dict[str, PlanningArtifact] = {}
        self.inputs: dict[str, PlanningArtifact] = {}
        self.constraints: dict[str, PlanningArtifact] = {}
        self.assumptions: dict[str, Assumption] = {}
        self.plans: dict[str, CandidatePlan] = {}
        self.steps: dict[str, PlanStep] = {}
        self.dependencies: dict[str, PlanningArtifact] = {}
        self.resources: dict[str, PlanningArtifact] = {}
        self.schedules: dict[str, PlanningArtifact] = {}
        self.risks: dict[str, PlanningArtifact] = {}
        self.scenarios: dict[str, PlanningArtifact] = {}
        self.simulations: dict[str, PlanningArtifact] = {}
        self.comparisons: dict[str, PlanningArtifact] = {}
        self.validations: dict[str, PlanningArtifact] = {}
        self.evaluations: dict[str, Evaluation] = {}
        self.recommendations: dict[str, PlanningArtifact] = {}
        self.reviews: dict[str, PlanningArtifact] = {}
        self.approvals: dict[str, Approval] = {}
        self.versions: dict[str, PlanningArtifact] = {}
        self.handoffs: dict[str, ReferenceHandoff] = {}
        self.history: list[dict[str, Any]] = []
        self.audit: list[dict[str, Any]] = []
        self.metrics = PlanningMetrics()

    @staticmethod
    def _require(context: PlanningContext, write: bool = False) -> None:
        permissions = context.permissions
        required = (
            "tiktok:autonomous-planning:write"
            if write
            else "tiktok:autonomous-planning:read"
        )
        if (
            required not in permissions
            and "tiktok:autonomous-planning:admin" not in permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    @staticmethod
    def _scoped(item: object, context: PlanningContext) -> None:
        if (
            getattr(item, "tenant", None) != context.tenant
            or getattr(item, "workspace", None) != context.workspace
        ):
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _record(self, context: PlanningContext, action: str, resource: str) -> None:
        self.audit.append(
            {
                "timestamp": utcnow(),
                "actor": context.actor,
                "tenant": context.tenant,
                "workspace": context.workspace,
                "action": action,
                "resource": resource,
                "advisory_only": True,
                "execution_authorized": False,
            }
        )

    def _add(
        self,
        store_name: str,
        item: T,
        context: PlanningContext,
        metric: str | None = None,
    ) -> T:
        self._require(context, write=True)
        self._scoped(item, context)
        store: dict[str, Any] = getattr(self, store_name)
        if item.id in store:
            raise ValueError(f"{store_name} ID must be unique.")
        store[item.id] = item
        self.history.append(
            {"type": store_name, **asdict(item)}  # type: ignore[call-overload]
        )
        if metric:
            self.metrics.increment(metric)
        self._record(context, f"{store_name}.recorded", item.id)
        return item

    def create_profile(
        self, item: PlanningProfile, context: PlanningContext
    ) -> PlanningProfile:
        if not 1 <= item.time_horizon_days <= self.max_horizon_days:
            raise ValueError("Planning horizon exceeds the configured bound.")
        if item.version < 1:
            raise ValueError("Version must be positive.")
        validate_safe_mapping(item.metadata)
        return self._add(
            "profiles", item, context, "tiktok_autonomous_planning_profiles_total"
        )

    def collect_inputs(
        self, context: PlanningContext
    ) -> dict[str, tuple[dict[str, object], ...]]:
        self._require(context)
        result = {
            name: adapter.read_references(context, limit=self.max_results)
            for name, adapter in self.sources.items()
        }
        if any(
            row.get("tenant") != context.tenant
            or row.get("workspace") != context.workspace
            for rows in result.values()
            for row in rows
        ):
            raise PermissionError("Adapter returned data outside scope.")
        self._record(context, "inputs.collected", "approved-sources")
        return result

    def add_artifact(
        self, resource: str, item: PlanningArtifact, context: PlanningContext
    ) -> PlanningArtifact:
        if resource not in RESOURCE_NAMES or resource in {
            "profiles",
            "assumptions",
            "plans",
            "steps",
            "evaluations",
            "approvals",
            "handoffs",
        }:
            raise ValueError("Unsupported generic planning artifact.")
        if item.version < 1:
            raise ValueError("Version must be positive.")
        for reference in item.references:
            validate_reference(reference)
        validate_safe_mapping(item.data)
        return self._add(resource, item, context)

    def add_assumption(self, item: Assumption, context: PlanningContext) -> Assumption:
        validate_reference(item.evidence_reference)
        if not 0 <= item.confidence <= 1:
            raise ValueError("Assumption confidence must be within [0, 1].")
        if item.validation_status.casefold() == "fact":
            raise ValueError("Assumptions must never be presented as facts.")
        return self._add("assumptions", item, context)

    def add_plan(self, item: CandidatePlan, context: PlanningContext) -> CandidatePlan:
        if len(self.plans) >= self.max_plans:
            raise ValueError("Bounded plan count exceeded.")
        if not 1 <= item.planning_horizon_days <= self.max_horizon_days:
            raise ValueError("Planning horizon exceeds the configured bound.")
        if not 0 <= item.confidence <= 1:
            raise ValueError("Plan confidence must be within [0, 1].")
        if not item.advisory_only or item.execution_authorized:
            raise ValueError("Plans must remain advisory and non-executable.")
        return self._add(
            "plans", item, context, "tiktok_autonomous_planning_plans_total"
        )

    def add_step(self, item: PlanStep, context: PlanningContext) -> PlanStep:
        plan_id = item.plan_reference.rsplit("/", 1)[-1]
        if plan_id not in self.plans:
            raise ValueError("Plan step has an invalid plan reference.")
        if (
            sum(
                1
                for step in self.steps.values()
                if step.plan_reference == item.plan_reference
            )
            >= self.max_steps_per_plan
        ):
            raise ValueError("Bounded step count exceeded.")
        if item.duration_estimate_minutes < 0 or item.sequence < 1:
            raise ValueError("Step estimates and sequence must be valid.")
        validate_safe_mapping(item.resource_estimate)
        if not item.planning_artifact_only or item.execution_authorized:
            raise ValueError("Plan steps must never invoke runtime capabilities.")
        return self._add(
            "steps", item, context, "tiktok_autonomous_planning_steps_total"
        )

    def validate_dependencies(
        self, plan_reference: str, context: PlanningContext
    ) -> dict[str, Any]:
        self._require(context)
        steps = [s for s in self.steps.values() if s.plan_reference == plan_reference]
        ids = {s.id for s in steps}
        missing: set[str] = set()
        graph: dict[str, set[str]] = {}
        for step in steps:
            dependencies = {
                ref.rsplit("/", 1)[-1] for ref in step.dependency_references
            }
            missing.update(dependencies - ids)
            graph[step.id] = dependencies & ids
        visiting: set[str] = set()
        visited: set[str] = set()

        def circular(node: str) -> bool:
            if node in visiting:
                return True
            if node in visited:
                return False
            visiting.add(node)
            found = any(circular(dep) for dep in graph[node])
            visiting.remove(node)
            visited.add(node)
            return found

        cycles = any(circular(node) for node in graph)
        result = {
            "missing_dependencies": sorted(missing),
            "circular_dependencies": cycles,
            "valid": not missing and not cycles,
        }
        if not result["valid"]:
            self.metrics.increment(
                "tiktok_autonomous_planning_validation_failures_total"
            )
        self._record(context, "dependencies.validated", plan_reference)
        return result

    def simulate(
        self, item: PlanningArtifact, context: PlanningContext
    ) -> PlanningArtifact:
        started = perf_counter()
        if item.kind not in {
            "timeline",
            "capacity",
            "resource_estimates",
            "dependency_flow",
            "constraint_satisfaction",
            "risk_exposure",
            "recovery_readiness",
            "approval_latency",
            "schedule_feasibility",
            "objective_coverage",
        }:
            raise ValueError("Unsupported bounded offline simulation.")
        if (
            item.data.get("live_tiktok")
            or item.data.get("browser_execution")
            or item.data.get("account_activity")
        ):
            raise ValueError("Simulations must be deterministic and offline.")
        result = self._add(
            "simulations", item, context, "tiktok_autonomous_planning_simulations_total"
        )
        self.metrics.observe(
            "tiktok_autonomous_planning_analysis_seconds", perf_counter() - started
        )
        return result

    def evaluate(self, item: Evaluation, context: PlanningContext) -> Evaluation:
        if set(item.scores) != set(SCORE_NAMES):
            raise ValueError("Every explainable plan-quality score is required.")
        if any(not 0 <= score <= 1 for score in item.scores.values()):
            raise ValueError("Evaluation scores must be within [0, 1].")
        if set(item.breakdown) != set(SCORE_NAMES) or any(
            not value for value in item.breakdown.values()
        ):
            raise ValueError("Every score requires a transparent breakdown.")
        expected = mean(item.scores.values())
        if abs(expected - item.overall_plan_quality) > 1e-9:
            raise ValueError(
                "Overall plan quality must equal the transparent score mean."
            )
        result = self._add("evaluations", item, context)
        self.metrics.observe("tiktok_autonomous_planning_plan_quality", expected)
        for metric in (
            "constraint_compliance",
            "resource_feasibility",
            "schedule_feasibility",
        ):
            self.metrics.observe(
                f"tiktok_autonomous_planning_{metric}", item.scores[metric]
            )
        return result

    def approve_reference(self, item: Approval, context: PlanningContext) -> Approval:
        if item.decision not in {"approved_reference", "rejected"}:
            raise ValueError("Approval decision is limited to the planning artifact.")
        if item.execution_authorized:
            raise ValueError("Planning approval does not authorize execution.")
        validate_reference(item.audit_reference)
        return self._add(
            "approvals", item, context, "tiktok_autonomous_planning_approvals_total"
        )

    def handoff(
        self, item: ReferenceHandoff, context: PlanningContext
    ) -> ReferenceHandoff:
        if item.destination not in HANDOFF_DESTINATIONS:
            raise ValueError("Unsupported planning handoff destination.")
        if not item.reference_only or item.triggered:
            raise ValueError(
                "Handoffs are reference-only and cannot trigger execution."
            )
        validate_reference(item.reference)
        return self._add("handoffs", item, context)

    def items(
        self,
        store: Mapping[str, object],
        context: PlanningContext,
        *,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        self._require(context)
        bounded = self.max_results if limit is None else limit
        if not 1 <= bounded <= self.max_results:
            raise ValueError("Requested result size exceeds the configured bound.")
        return [
            asdict(item)  # type: ignore[call-overload]
            for item in store.values()
            if getattr(item, "tenant", None) == context.tenant
            and getattr(item, "workspace", None) == context.workspace
        ][:bounded]

    def get_history(self, context: PlanningContext) -> list[dict[str, Any]]:
        self._require(context)
        return [
            entry
            for entry in self.history
            if entry.get("tenant") == context.tenant
            and entry.get("workspace") == context.workspace
        ][: self.max_results]

    def analytics(self, context: PlanningContext) -> dict[str, Any]:
        plans = self.items(self.plans, context)
        evaluations = self.items(self.evaluations, context)
        return {
            "profiles_total": len(self.items(self.profiles, context)),
            "candidate_plans_total": len(plans),
            "plans_ready_for_review": sum(
                p["status"] == PlanningStatus.READY_FOR_REVIEW for p in plans
            ),
            "plans_approved_as_references": sum(
                p["status"] == PlanningStatus.APPROVED_REFERENCE for p in plans
            ),
            "plans_rejected": sum(
                p["status"] == PlanningStatus.REJECTED for p in plans
            ),
            "plans_superseded": sum(
                p["status"] == PlanningStatus.SUPERSEDED for p in plans
            ),
            "simulations_total": len(self.items(self.simulations, context)),
            "validation_failures": self.metrics.values[
                "tiktok_autonomous_planning_validation_failures_total"
            ],
            "average_plan_quality": mean(e["overall_plan_quality"] for e in evaluations)
            if evaluations
            else 0.0,
            "advisory_only": True,
            "execution_authorized": False,
        }

    def dashboard(self, context: PlanningContext) -> dict[str, Any]:
        return {
            "planning_overview": {
                **self.analytics(context),
                "automatic_approval": False,
                "direct_execution": False,
                "publishing": False,
                "outreach": False,
                "browser_actions": False,
                "account_actions": False,
                "scheduler_mutation": False,
                "resource_allocation": False,
                "runtime_mutation": False,
                "restriction_bypass": False,
                "pause_and_kill_switch_aware": True,
            },
            "sections": (
                "Planning Overview",
                "Profiles",
                "Objectives",
                "Inputs",
                "Constraints",
                "Assumptions",
                "Candidate Plans",
                "Plan Steps",
                "Dependencies",
                "Resources",
                "Schedules",
                "Risks",
                "Scenarios",
                "Simulations",
                "Comparisons",
                "Validations",
                "Evaluations",
                "Recommendations",
                "Reviews",
                "Approvals",
                "Versions",
                "Handoffs",
                "History",
                "Analytics",
            ),
        }
