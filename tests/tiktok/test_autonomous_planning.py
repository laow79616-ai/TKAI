"""Offline safety and integration tests for autonomous planning."""

from datetime import datetime, timedelta, timezone

import pytest

from tiktok.autonomous_planning import (
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
    TikTokAutonomousPlanningCenter,
)
from tiktok.autonomous_planning.adapters import (
    PLANNING_SOURCES,
    ReferenceOnlyPlanningSource,
)
from tiktok.autonomous_planning.api import ROUTES, register_autonomous_planning_routes
from tiktok.autonomous_planning.metrics import METRIC_NAMES
from tiktok.autonomous_planning.service import SCORE_NAMES

NOW = datetime(2026, 7, 29, tzinfo=timezone.utc)


def context(
    workspace: str = "workspace",
    permissions: frozenset[str] = frozenset({"tiktok:autonomous-planning:admin"}),
) -> PlanningContext:
    return PlanningContext("tenant", workspace, "planner", permissions)


def configured() -> TikTokAutonomousPlanningCenter:
    service = TikTokAutonomousPlanningCenter(
        max_horizon_days=90, max_plans=2, max_steps_per_plan=2
    )
    service.create_profile(
        PlanningProfile(
            "profile",
            "Quarter plan",
            "Advisory",
            "tenant",
            "workspace",
            "owner",
            "growth",
            30,
            "bounded",
        ),
        context(),
    )
    service.add_plan(
        CandidatePlan(
            "plan",
            "tenant",
            "workspace",
            "profile://profile",
            ("objective://approved/1",),
            ("input://approved/1",),
            ("constraint://1",),
            ("assumption://1",),
            30,
            "high",
            PlanningStatus.READY_FOR_REVIEW,
            0.8,
            "medium",
            "Bounded candidate.",
        ),
        context(),
    )
    return service


def test_sources_are_scoped_bounded_read_only_and_non_executable() -> None:
    service = TikTokAutonomousPlanningCenter()
    rows = service.collect_inputs(context())
    assert set(rows) == set(PLANNING_SOURCES)
    assert all(
        row["read_only"] and row["reference_only"] and not row["execution"]
        for values in rows.values()
        for row in values
    )
    adapter = ReferenceOnlyPlanningSource("mission_engine")
    assert not hasattr(adapter, "execute")
    assert not hasattr(adapter, "publish")
    assert not hasattr(adapter, "schedule")
    assert not hasattr(adapter, "allocate")


def test_profiles_enforce_bounds_scope_rbac_and_secret_filtering() -> None:
    service = TikTokAutonomousPlanningCenter(max_horizon_days=30)
    with pytest.raises(ValueError, match="horizon"):
        service.create_profile(
            PlanningProfile("p", "P", "D", "tenant", "workspace", "o", "s", 31, "m"),
            context(),
        )
    with pytest.raises(ValueError, match="Secrets"):
        service.create_profile(
            PlanningProfile(
                "p",
                "P",
                "D",
                "tenant",
                "workspace",
                "o",
                "s",
                1,
                "m",
                metadata={"cookie": "x"},
            ),
            context(),
        )
    service.create_profile(
        PlanningProfile("p", "P", "D", "tenant", "workspace", "o", "s", 1, "m"),
        context(),
    )
    with pytest.raises(PermissionError, match="RBAC"):
        service.analytics(context(permissions=frozenset()))
    assert service.items(service.profiles, context("other")) == []


def test_assumptions_are_evidenced_but_never_facts() -> None:
    service = TikTokAutonomousPlanningCenter()
    good = Assumption(
        "a",
        "tenant",
        "workspace",
        "Capacity remains stable.",
        "forecast",
        "forecast://1",
        0.7,
        NOW + timedelta(days=7),
        "unvalidated",
        "Delay",
        "owner",
    )
    service.add_assumption(good, context())
    with pytest.raises(ValueError, match="facts"):
        service.add_assumption(
            Assumption(
                "fact",
                "tenant",
                "workspace",
                "Claim",
                "x",
                "evidence://1",
                1,
                NOW,
                "fact",
                "risk",
                "owner",
            ),
            context(),
        )


def test_plans_steps_and_approvals_never_authorize_execution() -> None:
    service = configured()
    step = PlanStep(
        "step",
        "tenant",
        "workspace",
        "plan://plan",
        "Review",
        "Human review",
        "review",
        "objective://approved/1",
        (),
        ("capability://review",),
        {"review_hours": 1},
        60,
        "window://1",
        ("constraint://1",),
        ("risk://1",),
        "valid",
        "explicit",
        None,
        1,
    )
    assert service.add_step(step, context()).planning_artifact_only
    with pytest.raises(ValueError, match="runtime"):
        service.add_step(
            PlanStep(
                "bad",
                "tenant",
                "workspace",
                "plan://plan",
                "Run",
                "Run",
                "runtime",
                "objective://approved/1",
                (),
                (),
                {},
                1,
                "window://1",
                (),
                (),
                "valid",
                "explicit",
                None,
                2,
                execution_authorized=True,
            ),
            context(),
        )
    approval = service.approve_reference(
        Approval(
            "approval",
            "tenant",
            "workspace",
            "plan://plan",
            1,
            "artifact",
            "reviewer",
            "approved_reference",
            (),
            None,
            NOW,
            "audit://1",
        ),
        context(),
    )
    assert not approval.execution_authorized


def test_dependency_validation_detects_missing_and_cycles() -> None:
    service = configured()
    base = dict(
        tenant="tenant",
        workspace="workspace",
        plan_reference="plan://plan",
        name="Step",
        description="Plan only",
        step_type="review",
        objective_reference="objective://1",
        required_capability_references=(),
        resource_estimate={},
        duration_estimate_minutes=1,
        schedule_window="window://1",
        constraint_references=(),
        risk_references=(),
        validation_status="pending",
        approval_requirement="explicit",
        handoff_reference=None,
    )
    service.add_step(
        PlanStep(id="a", dependency_references=("step://missing",), sequence=1, **base),
        context(),
    )
    assert service.validate_dependencies("plan://plan", context())[
        "missing_dependencies"
    ] == ["missing"]
    other = configured()
    other.add_step(
        PlanStep(id="a", dependency_references=("step://b",), sequence=1, **base),
        context(),
    )
    other.add_step(
        PlanStep(id="b", dependency_references=("step://a",), sequence=2, **base),
        context(),
    )
    assert other.validate_dependencies("plan://plan", context())[
        "circular_dependencies"
    ]


def test_offline_simulation_evaluation_and_reference_handoff() -> None:
    service = configured()
    simulation = PlanningArtifact(
        "sim",
        "tenant",
        "workspace",
        "timeline",
        "Timeline",
        data={"deterministic": True},
    )
    service.simulate(simulation, context())
    with pytest.raises(ValueError, match="offline"):
        service.simulate(
            PlanningArtifact(
                "live",
                "tenant",
                "workspace",
                "timeline",
                "Live",
                data={"live_tiktok": True},
            ),
            context(),
        )
    scores = {name: 0.8 for name in SCORE_NAMES}
    evaluation = service.evaluate(
        Evaluation(
            "eval",
            "tenant",
            "workspace",
            "plan://plan",
            scores,
            {name: {"weight": 1, "reason": "bounded"} for name in SCORE_NAMES},
            0.8,
        ),
        context(),
    )
    assert evaluation.breakdown
    handoff = service.handoff(
        ReferenceHandoff(
            "h", "tenant", "workspace", "plan://plan", "mission_engine", "plan://plan"
        ),
        context(),
    )
    assert handoff.reference_only and not handoff.triggered


def test_dashboard_api_metrics_history_and_no_execution_route() -> None:
    class App:
        def __init__(self) -> None:
            self.routes: list[tuple[str, list[str]]] = []

        def add_api_route(self, path: str, endpoint: object, **kwargs: object) -> None:
            self.routes.append((path, list(kwargs["methods"])))

    service = configured()
    dashboard = service.dashboard(context())
    assert dashboard["planning_overview"]["advisory_only"]
    assert not dashboard["planning_overview"]["direct_execution"]
    assert dashboard["planning_overview"]["pause_and_kill_switch_aware"]
    app = App()
    register_autonomous_planning_routes(app, service)
    paths = {path for path, _ in app.routes}
    assert set(ROUTES).issubset(paths)
    assert not any("execution" in path for path in paths)
    assert all(methods == ["GET"] for _, methods in app.routes)
    assert all(name in service.metrics.render_prometheus() for name in METRIC_NAMES)
    assert service.get_history(context())
