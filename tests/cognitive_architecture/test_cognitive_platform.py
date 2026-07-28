import pytest

from cognitive_architecture import (
    Adaptation,
    Attention,
    CognitiveArchitecturePlatform,
    CognitiveModel,
    CognitiveScope,
    CognitiveStatus,
    Decision,
    LearningCycle,
    Memory,
    Metacognition,
    Monitoring,
    Perception,
    Plan,
    Reasoning,
    ReasoningMode,
    Reflection,
)


@pytest.fixture
def system():
    platform = CognitiveArchitecturePlatform()
    scope = CognitiveScope(
        "tenant",
        "workspace",
        "owner",
        frozenset(
            {
                "cognitive:read",
                "cognitive:write",
                "cognitive:execute",
                "cognitive:reason",
                "cognitive:plan",
                "cognitive:learn",
                "cognitive:reflect",
                "cognitive:decide",
                "cognitive:adapt",
                "cognitive:monitor",
            }
        ),
    )
    model = CognitiveModel(
        "model",
        "Enterprise Cognition",
        "Cognitive control plane",
        "tenant",
        "workspace",
        "owner",
        {"perception": {}, "reasoning": {}, "decision": {}},
        metadata={"classification": "internal"},
    )
    platform.create_model(model, scope)
    return platform, scope


def test_model_lifecycle_validation_and_isolation(system):
    platform, scope = system
    for status in (
        CognitiveStatus.TRAINING,
        CognitiveStatus.READY,
        CognitiveStatus.RUNNING,
        CognitiveStatus.PAUSED,
        CognitiveStatus.ARCHIVED,
        CognitiveStatus.DELETED,
    ):
        platform.set_status("model", status, scope)
    assert platform.models["model"].status is CognitiveStatus.DELETED
    with pytest.raises(ValueError):
        platform.set_status("model", CognitiveStatus.DRAFT, scope)
    foreign = CognitiveScope("other", "workspace", "intruder")
    assert platform.list_models(foreign) == []
    with pytest.raises(PermissionError):
        platform.set_status("model", CognitiveStatus.READY, foreign)


def test_perception_attention_and_memory(system):
    platform, scope = system
    perception = platform.perceive(
        Perception(
            "perception",
            "model",
            "tenant",
            "workspace",
            ("event://orders",),
            "z-score",
            ("volume", "risk"),
            {"customer": "knowledge://customer"},
            0.93,
        ),
        scope,
    )
    attention = platform.focus(
        Attention(
            "attention",
            "model",
            "tenant",
            "workspace",
            100,
            32,
            ("risk",),
            {"minimum_confidence": 0.8},
            "priority",
        ),
        scope,
    )
    memory = platform.remember(
        Memory(
            "memory",
            "model",
            "tenant",
            "workspace",
            {"current_order": "42"},
            "memory://long-term/42",
            ("episode://42",),
            ("concept://risk",),
            "P90D",
            "semantic_then_episodic",
        ),
        scope,
    )
    assert perception.confidence == 0.93
    assert attention.focus_window == 32
    assert memory.long_term_memory_reference.startswith("memory://")
    with pytest.raises(ValueError):
        platform.perceive(
            Perception(
                "bad",
                "model",
                "tenant",
                "workspace",
                (),
                "none",
                (),
                {},
                2,
            ),
            scope,
        )


def test_reasoning_planning_learning_and_reflection(system):
    platform, scope = system
    reasoning = platform.reason(
        Reasoning(
            "reasoning",
            "model",
            "tenant",
            "workspace",
            ReasoningMode.PROBABILISTIC,
            ("order value is high", "customer risk is elevated"),
            "manual review",
            0.88,
            ("risk < policy limit",),
            ("evidence://order/42", "evidence://customer/7"),
        ),
        scope,
    )
    plan = platform.create_plan(
        Plan(
            "plan",
            "model",
            "tenant",
            "workspace",
            ("validate", "approve"),
            {"validate": (), "approve": ("validate",)},
            ("approved",),
            {"approve": ("validate",)},
            {"policy": 0.2},
            {"reviewers": 1},
        ),
        scope,
    )
    learning = platform.learn(
        LearningCycle(
            "learning",
            "model",
            "tenant",
            "workspace",
            {"reviewer": "correct"},
            {"accuracy": 0.8},
            {"accepted": True},
            ("raise calibration sample",),
            "1.0.1",
        ),
        scope,
    )
    reflection = platform.reflect(
        Reflection(
            "reflection",
            "model",
            "tenant",
            "workspace",
            {"outcome": "approved"},
            ("latency exceeded target",),
            ("preload policy context",),
            ("tune focus window",),
            0.86,
        ),
        scope,
    )
    assert reasoning.mode is ReasoningMode.PROBABILISTIC
    assert plan.task_graph["approve"] == ("validate",)
    assert learning.version_tracking == "1.0.1"
    assert reflection.improvement_suggestions
    with pytest.raises(ValueError):
        platform.create_plan(
            Plan(
                "cyclic",
                "model",
                "tenant",
                "workspace",
                ("a",),
                {"a": ("b",), "b": ("a",)},
            ),
            scope,
        )


def test_decision_adaptation_monitoring_metacognition_and_dashboard(system):
    platform, scope = system
    decision = platform.decide(
        Decision(
            "decision",
            "model",
            "tenant",
            "workspace",
            {"approve": 1, "review": 1},
            {"approve": 0.7, "review": 0.9},
            True,
            "approved",
            "plan",
            evidence_references=("evidence://decision/42",),
        ),
        scope,
    )
    platform.adapt(
        Adaptation(
            "adaptation",
            "model",
            "tenant",
            "workspace",
            {"review_required": True},
            {"confidence": 0.85},
            {"market": "volatile"},
            "risk_aware",
        ),
        scope,
    )
    platform.monitor(
        Monitoring(
            "monitor",
            "model",
            "tenant",
            "workspace",
            "healthy",
            0.98,
            0.12,
            {"cpu": 0.3, "memory": 128},
        ),
        scope,
    )
    platform.evaluate_metacognition(
        Metacognition(
            "meta",
            "model",
            "tenant",
            "workspace",
            0.91,
            0.89,
            ("selection_bias",),
            "explainability://trace/42",
        ),
        scope,
    )
    dashboard = platform.dashboard(scope)
    assert decision.selected == "review"
    assert dashboard["health"]["status"] == "healthy"
    assert {
        "perception",
        "attention",
        "memory",
        "reasoning",
        "planning",
        "learning",
        "reflection",
        "decision",
        "adaptation",
        "metacognition",
        "health",
    } <= dashboard.keys()
    assert platform.metrics.snapshot()["cognitive_decisions_total"] == 1


def test_security_policy_validation_evidence_audit_and_no_secrets(system):
    platform, scope = system
    with pytest.raises(PermissionError):
        platform.decide(
            Decision(
                "blocked",
                "model",
                "tenant",
                "workspace",
                {"approve": 1},
                {"approve": 1},
                False,
                "denied",
                "plan",
                evidence_references=("evidence://1",),
            ),
            scope,
        )
    platform._audit(
        "security.validation",
        scope,
        model_id="model",
        secret="must-not-appear",
        token_value="must-not-appear",
    )
    assert "must-not-appear" not in str(platform.audit)
    assert platform.metrics.snapshot()["cognitive_failures_total"] == 1
