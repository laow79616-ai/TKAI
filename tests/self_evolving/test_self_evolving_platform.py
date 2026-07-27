import pytest

from self_evolving import (
    Adaptation,
    ApprovalState,
    Evaluation,
    EvolutionCycle,
    EvolutionProfile,
    EvolutionScope,
    EvolutionStatus,
    Experiment,
    Feedback,
    LearningCycle,
    MonitoringRecord,
    Mutation,
    Optimization,
    SelfEvolvingPlatform,
)


@pytest.fixture
def platform():
    return SelfEvolvingPlatform()


@pytest.fixture
def scope():
    return EvolutionScope(
        "tenant-a",
        "workspace-a",
        "owner",
        frozenset(
            {
                "self_evolving:read",
                "self_evolving:write",
                "self_evolving:evolve",
                "self_evolving:learn",
                "self_evolving:adapt",
                "self_evolving:mutate",
                "self_evolving:experiment",
                "self_evolving:evaluate",
                "self_evolving:optimize",
                "self_evolving:feedback",
                "self_evolving:monitor",
                "self_evolving:safety",
                "self_evolving:rollback",
            }
        ),
    )


@pytest.fixture
def profile(platform, scope):
    return platform.create_profile(
        EvolutionProfile(
            "profile-1",
            "Enterprise Evolver",
            "Continuously improves governed intelligence",
            scope.tenant,
            scope.workspace,
            scope.actor,
            0,
            3,
        ),
        scope,
    )


def test_profile_lifecycle_and_isolation(platform, scope, profile):
    for status in (
        EvolutionStatus.LEARNING,
        EvolutionStatus.EVALUATING,
        EvolutionStatus.EVOLVING,
        EvolutionStatus.VALIDATED,
        EvolutionStatus.RUNNING,
        EvolutionStatus.PAUSED,
        EvolutionStatus.ARCHIVED,
        EvolutionStatus.DELETED,
    ):
        platform.set_status(profile.id, status, scope)
    assert profile.status is EvolutionStatus.DELETED
    other = EvolutionScope("tenant-b", scope.workspace, "intruder")
    assert platform.list_profiles(other) == []
    with pytest.raises(PermissionError):
        platform.set_status(profile.id, EvolutionStatus.LEARNING, other)


def test_learning_adaptation_feedback_and_monitoring(platform, scope, profile):
    platform.learn(
        LearningCycle(
            "learn-1",
            profile.id,
            scope.tenant,
            scope.workspace,
            ("outcomes",),
            {"quality": 0.9},
            ("experience-1",),
            {"human": "accepted"},
            "1.0.0",
        ),
        scope,
    )
    platform.adapt(
        Adaptation(
            "adapt-1",
            profile.id,
            scope.tenant,
            scope.workspace,
            {"region": "cn"},
            {"risk": "conservative"},
            {"cpu": 2},
            {"confidence": 0.8},
            "safe-best",
        ),
        scope,
    )
    platform.feedback(
        Feedback(
            "feedback-1",
            profile.id,
            scope.tenant,
            scope.workspace,
            human_feedback=("useful",),
            telemetry={"success": 1},
        ),
        scope,
    )
    platform.monitor(
        MonitoringRecord(
            "monitor-1",
            profile.id,
            scope.tenant,
            scope.workspace,
            "healthy",
            0.5,
            1,
            (),
            {"cpu": 0.4},
            0.01,
        ),
        scope,
    )
    dashboard = platform.dashboard(scope)
    assert dashboard["monitoring"]["health"] == "healthy"
    assert dashboard["metrics"]["self_learning_cycles_total"] == 1


def test_controlled_mutation_experiment_evaluation_and_optimization(
    platform, scope, profile
):
    platform.mutate(
        Mutation(
            "mutation-1",
            profile.id,
            scope.tenant,
            scope.workspace,
            ("candidate-a", "candidate-b"),
            {"candidate-a": 0.8},
            "checkpoint://1",
            True,
        ),
        scope,
    )
    platform.experiment(
        Experiment(
            "experiment-1",
            profile.id,
            scope.tenant,
            scope.workspace,
            "shadow",
            "Candidate improves quality",
            {"baseline": 0.7},
            ApprovalState.APPROVED,
            "audit://1",
        ),
        scope,
    )
    platform.evaluate(
        Evaluation(
            "evaluation-1",
            profile.id,
            scope.tenant,
            scope.workspace,
            {"reasoning": 0.9},
            {"regression": 0.0},
            {"risk": 0.1},
            {"quality": 0.9},
            0.9,
        ),
        scope,
    )
    platform.optimize(
        Optimization(
            "optimization-1",
            profile.id,
            scope.tenant,
            scope.workspace,
            1.1,
            0.2,
            0.3,
            {"cpu": 0.5},
            {"joules": 2.0},
            {"policy": "efficient"},
        ),
        scope,
    )
    assert platform.metrics.snapshot()["self_experiments_total"] == 1
    assert platform.metrics.snapshot()["self_optimizations_total"] == 1


def test_evolution_lineage_rollback_and_kill_switch(platform, scope, profile):
    cycle = EvolutionCycle(
        "evolution-1",
        profile.id,
        scope.tenant,
        scope.workspace,
        capability_evolution={"reasoning": "enhanced"},
        policy_evolution={"risk": "bounded"},
        knowledge_evolution={"graph": "expanded"},
        workflow_evolution={"planning": "adaptive"},
        architecture_evolution={"runtime": "isolated"},
        parent_version="1.0.0",
        candidate_version="1.1.0",
        approval_state=ApprovalState.APPROVED,
    )
    platform.evolve(cycle, scope)
    assert profile.generation == 1
    assert platform.version_lineage == {"1.1.0": "1.0.0"}
    platform.rollback(profile.id, "1.0.0", scope)
    assert profile.version == "1.0.0"
    assert platform.metrics.snapshot()["self_rollbacks_total"] == 1
    platform.activate_kill_switch(profile.id, scope, "risk threshold exceeded")
    with pytest.raises(RuntimeError):
        platform.learn(
            LearningCycle(
                "blocked",
                profile.id,
                scope.tenant,
                scope.workspace,
                ("x",),
                {"x": 1},
                (),
                {},
                "1.0.0",
            ),
            scope,
        )
    platform.release_kill_switch(profile.id, scope)
    assert profile.id not in platform.kill_switches


def test_safety_validation_and_rbac(platform, scope, profile):
    denied = EvolutionCycle(
        "denied",
        profile.id,
        scope.tenant,
        scope.workspace,
        parent_version="1.0.0",
        candidate_version="2.0.0",
    )
    with pytest.raises(PermissionError):
        platform.evolve(denied, scope)
    with pytest.raises(PermissionError):
        platform.mutate(
            Mutation(
                "unsafe",
                profile.id,
                scope.tenant,
                scope.workspace,
                ("x",),
                {"x": 1},
                "",
                False,
            ),
            scope,
        )
    with pytest.raises(PermissionError):
        platform.create_profile(
            EvolutionProfile("x", "x", "", scope.tenant, scope.workspace, "x", 0, 1),
            EvolutionScope(scope.tenant, scope.workspace, "reader"),
        )
