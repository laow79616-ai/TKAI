import pytest

from autonomous_intelligence import (
    Adaptation,
    ApprovalState,
    AutonomousIntelligencePlatform,
    Awareness,
    Coordination,
    Execution,
    Goal,
    IntelligenceProfile,
    IntelligenceScope,
    IntelligenceStatus,
    Intent,
    LearningCycle,
    MonitoringRecord,
    Plan,
    Prediction,
    ReasoningRecord,
    Reflection,
)


@pytest.fixture
def system():
    platform = AutonomousIntelligencePlatform()
    permissions = frozenset(
        {
            "autonomous_intelligence:read",
            "autonomous_intelligence:write",
            "autonomous_intelligence:observe",
            "autonomous_intelligence:reason",
            "autonomous_intelligence:plan",
            "autonomous_intelligence:predict",
            "autonomous_intelligence:learn",
            "autonomous_intelligence:reflect",
            "autonomous_intelligence:adapt",
            "autonomous_intelligence:execute",
            "autonomous_intelligence:approve",
            "autonomous_intelligence:coordinate",
            "autonomous_intelligence:monitor",
        }
    )
    scope = IntelligenceScope("tenant", "workspace", "owner", permissions)
    platform.create_profile(
        IntelligenceProfile(
            "profile",
            "Enterprise Autonomy",
            "Governed intelligence",
            "tenant",
            "workspace",
            "owner",
            4,
            metadata={"classification": "internal"},
        ),
        scope,
    )
    return platform, scope


def test_profile_lifecycle_isolation_rbac_and_audit_redaction(system):
    platform, scope = system
    for status in (
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
    foreign = IntelligenceScope("other", "workspace", "intruder")
    assert platform.list_profiles(foreign) == []
    with pytest.raises(PermissionError):
        platform.set_status("profile", IntelligenceStatus.READY, foreign)
    platform._audit(
        "security.check",
        scope,
        secret="hidden",
        access_token="hidden",
        credential_key="hidden",
    )
    assert "hidden" not in str(platform.audit)


def test_awareness_intent_and_goals(system):
    platform, scope = system
    awareness = platform.observe(
        Awareness(
            "aware",
            "profile",
            "tenant",
            "workspace",
            {"market": "volatile"},
            {"customer": "priority"},
            {"cpu": 0.4},
            ("policy://risk",),
            {"fraud": 0.2},
            0.91,
        ),
        scope,
    )
    intent = platform.set_intent(
        Intent(
            "intent",
            "profile",
            "tenant",
            "workspace",
            "Protect revenue",
            ("reduce fraud",),
            100,
            ("no customer harm",),
            ("policy://risk",),
            ApprovalState.APPROVED,
        ),
        scope,
    )
    goal = platform.define_goal(
        Goal(
            "goal",
            "profile",
            "tenant",
            "workspace",
            ("trusted commerce",),
            ("review risky orders",),
            ("classify order",),
            ("reduce loss",),
            {"false_positive_rate": 0.02},
            0.25,
        ),
        scope,
    )
    assert awareness.confidence == 0.91
    assert intent.approval_state is ApprovalState.APPROVED
    assert goal.progress == 0.25
    with pytest.raises(PermissionError):
        platform.set_intent(
            Intent(
                "denied",
                "profile",
                "tenant",
                "workspace",
                "Unsafe",
                ("bypass",),
                1,
                approval_state=ApprovalState.DENIED,
            ),
            scope,
        )


def test_reasoning_planning_prediction_learning_reflection_adaptation(system):
    platform, scope = system
    reasoning = platform.reason(
        ReasoningRecord(
            "reason",
            "profile",
            "tenant",
            "workspace",
            ("evidence://order/42",),
            ("inspect", "evaluate", "decide"),
            True,
            {"fraud": 0.3},
            0.87,
            "trace://42",
        ),
        scope,
    )
    plan = platform.create_plan(
        Plan(
            "plan",
            "profile",
            "tenant",
            "workspace",
            ("validate", "decide"),
            {"validate": (), "decide": ("validate",)},
            ("decision",),
            {"decide": ("validate",)},
            {"validate": "2026-07-27T12:00:00Z"},
            {"objective": "minimize_latency"},
        ),
        scope,
    )
    prediction = platform.predict(
        Prediction(
            "prediction",
            "profile",
            "tenant",
            "workspace",
            {"approve": 0.8},
            {"fraud": 0.2},
            {"orders_per_second": 1000},
            {"growth": 0.1},
            0.84,
        ),
        scope,
    )
    learning = platform.learn(
        LearningCycle(
            "learning",
            "profile",
            "tenant",
            "workspace",
            ("continuous feedback",),
            {"approved": True},
            {"reviewer": "correct"},
            "1.0.1",
            ("increase calibration sample",),
        ),
        scope,
    )
    reflection = platform.reflect(
        Reflection(
            "reflection",
            "profile",
            "tenant",
            "workspace",
            {"result": "approved"},
            {"accuracy": 0.96},
            ("policy lookup latency",),
            ("preload policy",),
            0.9,
        ),
        scope,
    )
    adaptation = platform.adapt(
        Adaptation(
            "adapt",
            "profile",
            "tenant",
            "workspace",
            {"manual_review": True},
            "risk_aware",
            {"confidence": 0.85},
            {"workers": 2},
            "manual_review",
        ),
        scope,
    )
    assert reasoning.decision_trace_reference == "trace://42"
    assert plan.execution_graph["decide"] == ("validate",)
    assert prediction.confidence == 0.84
    assert learning.version_tracking == "1.0.1"
    assert reflection.lessons_learned
    assert adaptation.fallback_strategy == "manual_review"
    with pytest.raises(ValueError):
        platform.create_plan(
            Plan(
                "cyclic",
                "profile",
                "tenant",
                "workspace",
                ("a", "b"),
                {"a": ("b",), "b": ("a",)},
            ),
            scope,
        )


def test_execution_coordination_monitoring_dashboard_and_metrics(system):
    platform, scope = system
    execution = platform.execute(
        Execution(
            "execution",
            "profile",
            "tenant",
            "workspace",
            "parallel",
            ("validate", "notify"),
            "checkpoint://1",
            "rollback://1",
            "retry_then_manual",
            ("risk-approval",),
        ),
        scope,
    )
    assert execution.state == "completed"
    assert platform.rollback("execution", scope).state == "rolled_back"
    assert platform.recover("execution", scope).state == "recovered"
    platform.coordinate(
        Coordination(
            "coordination",
            "profile",
            "tenant",
            "workspace",
            ("agent-risk", "agent-notify"),
            "context://42",
            {"validate": "agent-risk", "notify": "agent-notify"},
            "consensus://42",
            "governance_vote",
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
            0.12,
            {"cpu": 0.3},
            (),
            (0.82, 0.87),
        ),
        scope,
    )
    dashboard = platform.dashboard(scope)
    assert dashboard["monitoring"]["health"] == "healthy"
    assert dashboard["execution"][0]["state"] == "recovered"
    metrics = platform.metrics.snapshot()
    assert metrics["autonomous_intelligence_profiles_total"] == 1
    assert metrics["autonomous_reasoning_total"] == 0
    assert metrics["autonomous_execution_total"] == 1


def test_approval_enforcement_and_policy_validation(system):
    platform, scope = system
    without_approval = IntelligenceScope(
        scope.tenant,
        scope.workspace,
        scope.actor,
        scope.permissions - {"autonomous_intelligence:approve"},
    )
    with pytest.raises(PermissionError):
        platform.execute(
            Execution(
                "blocked",
                "profile",
                "tenant",
                "workspace",
                "sequential",
                ("act",),
                "checkpoint://2",
                "rollback://2",
                "manual",
                ("approval",),
            ),
            without_approval,
        )
    with pytest.raises(PermissionError):
        platform.reason(
            ReasoningRecord(
                "unsafe",
                "profile",
                "tenant",
                "workspace",
                ("evidence://1",),
                ("decide",),
                False,
                {"risk": 0.1},
                0.8,
                "trace://unsafe",
            ),
            scope,
        )
