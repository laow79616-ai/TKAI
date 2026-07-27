import pytest

from super_intelligence import (
    Adaptation,
    Alignment,
    Capability,
    CollectiveReasoning,
    Coordination,
    Decision,
    Evaluation,
    IntelligenceProfile,
    IntelligenceScope,
    IntelligenceStatus,
    KnowledgeSynthesis,
    MonitoringRecord,
    Optimization,
    Prediction,
    SelfImprovement,
    StrategicPlan,
    SuperIntelligencePlatform,
    WorldModel,
)


@pytest.fixture
def system():
    permissions = frozenset(
        {
            "super_intelligence:read",
            "super_intelligence:write",
            "super_intelligence:reason",
            "super_intelligence:plan",
            "super_intelligence:model",
            "super_intelligence:synthesize",
            "super_intelligence:predict",
            "super_intelligence:optimize",
            "super_intelligence:coordinate",
            "super_intelligence:decide",
            "super_intelligence:approve",
            "super_intelligence:adapt",
            "super_intelligence:improve",
            "super_intelligence:align",
            "super_intelligence:evaluate",
            "super_intelligence:monitor",
        }
    )
    scope = IntelligenceScope("tenant", "workspace", "owner", permissions)
    platform = SuperIntelligencePlatform()
    platform.create_profile(
        IntelligenceProfile(
            "profile",
            "Enterprise Super Intelligence",
            "Governed intelligence",
            "tenant",
            "workspace",
            "owner",
            5,
            "collective-cognitive-v1",
            metadata={"classification": "internal"},
        ),
        scope,
    )
    return platform, scope


def test_lifecycle_isolation_rbac_and_audit_redaction(system) -> None:
    platform, scope = system
    for status in (
        IntelligenceStatus.TRAINING,
        IntelligenceStatus.LEARNING,
        IntelligenceStatus.READY,
        IntelligenceStatus.RUNNING,
        IntelligenceStatus.COMPLETED,
        IntelligenceStatus.ARCHIVED,
        IntelligenceStatus.DELETED,
    ):
        platform.set_status("profile", status, scope)
    with pytest.raises(ValueError):
        platform.set_status("profile", IntelligenceStatus.DRAFT, scope)
    assert (
        platform.list_profiles(IntelligenceScope("other", "workspace", "actor")) == []
    )
    platform._audit("security", scope, access_token="hidden", safe="visible")
    assert "hidden" not in str(platform.audit)


def test_capabilities_reasoning_planning_models_and_synthesis(system) -> None:
    platform, scope = system
    platform.register_capability(
        Capability("cap", "profile", "tenant", "workspace", "Scientific Reasoning", 5),
        scope,
    )
    platform.reason(
        CollectiveReasoning(
            "reason",
            "profile",
            "tenant",
            "workspace",
            ("agent-a", "agent-b"),
            ("evidence://a", "evidence://b"),
            "weighted-consensus",
            "human-arbitration",
            0.93,
            "trace://reason",
        ),
        scope,
    )
    platform.plan(
        StrategicPlan(
            "plan",
            "profile",
            "tenant",
            "workspace",
            "Grow safely",
            ("expand",),
            ("validate", "launch"),
            {"launch": ("validate",)},
            {"gpu": 0.5},
            ("base", "stress"),
            {"compliance": 0.2},
        ),
        scope,
    )
    platform.model_world(
        WorldModel(
            "world",
            "profile",
            "tenant",
            "workspace",
            {"market": "dynamic"},
            {"platform": "healthy"},
            {"revenue": "growing"},
            "twin://enterprise",
            {"scenario": "stress"},
            {"growth": 0.2},
        ),
        scope,
    )
    platform.synthesize(
        KnowledgeSynthesis(
            "knowledge",
            "profile",
            "tenant",
            "workspace",
            "graph://enterprise",
            ("schema://business",),
            ("evidence://a",),
            {"risk": ("finance", "security")},
            "versioned",
        ),
        scope,
    )
    assert platform.dashboard(scope)["reasoning"][0]["confidence"] == 0.93


def test_prediction_optimization_coordination_decision_and_adaptation(system) -> None:
    platform, scope = system
    platform.predict(
        Prediction(
            "prediction",
            "profile",
            "tenant",
            "workspace",
            {"risk": 0.2},
            {"requests": 1000},
            {"success": 0.9},
            {"growth": 0.1},
            0.88,
        ),
        scope,
    )
    platform.optimize(
        Optimization(
            "optimization",
            "profile",
            "tenant",
            "workspace",
            {"gpu": 0.2},
            {"savings": 0.3},
            {"p95": 0.25},
            {"energy": 0.15},
            {"policy": "balanced"},
        ),
        scope,
    )
    platform.coordinate(
        Coordination(
            "coordination",
            "profile",
            "tenant",
            "workspace",
            ("planner", "reviewer"),
            {"plan": "planner", "review": "reviewer"},
            "policy-negotiation",
            "memory://shared",
            "quorum",
        ),
        scope,
    )
    platform.decide(
        Decision(
            "decision",
            "profile",
            "tenant",
            "workspace",
            ("evidence://a",),
            True,
            ("human",),
            ("validate", "execute"),
            "rollback://decision",
        ),
        scope,
    )
    platform.adapt(
        Adaptation(
            "adapt",
            "profile",
            "tenant",
            "workspace",
            "risk-aware",
            {"market": "volatile"},
            {"confidence": 0.8},
            "human-review",
            True,
        ),
        scope,
    )
    metrics = platform.metrics.snapshot()
    assert metrics["super_predictions_total"] == 1
    assert metrics["super_optimizations_total"] == 1


def test_improvement_alignment_evaluation_monitoring_and_security(system) -> None:
    platform, scope = system
    platform.self_improve(
        SelfImprovement(
            "improve",
            "profile",
            "tenant",
            "workspace",
            {"accuracy": 0.95},
            {"review": "accepted"},
            ("Scientific Reasoning",),
            "model-v2",
            ("increase calibration data",),
        ),
        scope,
    )
    platform.align(
        Alignment(
            "alignment",
            "profile",
            "tenant",
            "workspace",
            ("trusted growth",),
            ("safety://core",),
            ("soc2",),
            ("fairness",),
            "human-owner",
            "audit://alignment",
        ),
        scope,
    )
    platform.evaluate(
        Evaluation(
            "evaluation",
            "profile",
            "tenant",
            "workspace",
            {"benchmark": 0.9},
            {"reasoning": 0.92},
            0.9,
            {"quality": 0.94},
            {"delta": 0.01},
        ),
        scope,
    )
    platform.monitor(
        MonitoringRecord(
            "monitor",
            "profile",
            "tenant",
            "workspace",
            "healthy",
            0.1,
            {"cpu": 0.3},
            (),
            {"reasoning": (0.8, 0.9)},
            "audit://monitor",
        ),
        scope,
    )
    dashboard = platform.dashboard(scope)
    assert dashboard["monitoring"]["health"] == "healthy"
    assert platform.metrics.snapshot()["super_self_improvements_total"] == 1
    assert platform.metrics.snapshot()["super_evaluations_total"] == 1
    without_approval = IntelligenceScope(
        scope.tenant,
        scope.workspace,
        scope.actor,
        scope.permissions - {"super_intelligence:approve"},
    )
    with pytest.raises(PermissionError):
        platform.decide(
            Decision(
                "blocked",
                "profile",
                "tenant",
                "workspace",
                ("evidence://a",),
                True,
                ("human",),
                ("execute",),
                "rollback://blocked",
            ),
            without_approval,
        )
