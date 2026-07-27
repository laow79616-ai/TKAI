import pytest

from self_optimization import (
    ApprovalState,
    CapacityPlan,
    CostRecord,
    Evaluation,
    Experiment,
    LatencyRecord,
    MonitoringRecord,
    OptimizationCycle,
    OptimizationProfile,
    OptimizationScope,
    OptimizationStatus,
    PerformanceRecord,
    Recommendation,
    ResourcePlan,
    SelfOptimizationPlatform,
    StrategyType,
)


@pytest.fixture
def platform():
    return SelfOptimizationPlatform()


@pytest.fixture
def scope():
    actions = {
        "write",
        "optimize",
        "resources",
        "performance",
        "cost",
        "latency",
        "capacity",
        "experiment",
        "recommend",
        "evaluate",
        "monitor",
        "safety",
        "rollback",
    }
    permissions = {"self_optimization:read"}
    permissions.update(f"self_optimization:{action}" for action in actions)
    return OptimizationScope(
        "tenant-a", "workspace-a", "owner", frozenset(permissions)
    )


@pytest.fixture
def profile(platform, scope):
    return platform.create_profile(
        OptimizationProfile(
            "profile-1",
            "Enterprise Optimizer",
            "Safely optimizes enterprise AI",
            scope.tenant,
            scope.workspace,
            scope.actor,
            "platform",
        ),
        scope,
    )


def test_lifecycle_rbac_and_isolation(platform, scope, profile):
    for status in (
        OptimizationStatus.ANALYZING,
        OptimizationStatus.OPTIMIZING,
        OptimizationStatus.VALIDATING,
        OptimizationStatus.RUNNING,
        OptimizationStatus.PAUSED,
        OptimizationStatus.ARCHIVED,
        OptimizationStatus.DELETED,
    ):
        platform.set_status(profile.id, status, scope)
    assert profile.status is OptimizationStatus.DELETED
    other = OptimizationScope("tenant-b", scope.workspace, "intruder")
    assert platform.list_profiles(other) == []
    with pytest.raises(PermissionError):
        platform.set_status(profile.id, OptimizationStatus.ANALYZING, other)


def test_optimization_lineage_metrics_rollback_and_kill_switch(
    platform, scope, profile
):
    platform.optimize(
        OptimizationCycle(
            "cycle-1",
            profile.id,
            scope.tenant,
            scope.workspace,
            StrategyType.HYBRID,
            performance_improvement=0.2,
            latency_improvement=0.1,
            cost_reduction=5,
            capacity_adjustment=2,
            resource_optimization={"cpu": 1},
            policy_optimization={"autoscale": True},
            parent_version="1.0.0",
            candidate_version="1.1.0",
            approval_state=ApprovalState.APPROVED,
            rollback_reference="checkpoint://1",
        ),
        scope,
    )
    assert profile.version == "1.1.0"
    metrics = platform.metrics.snapshot()
    assert metrics["self_optimization_cycles_total"] == 1
    assert metrics["self_cost_reduction_total"] == 5
    platform.rollback(profile.id, "1.0.0", scope)
    assert profile.status is OptimizationStatus.PAUSED
    platform.activate_kill_switch(profile.id, scope, "risk threshold")
    with pytest.raises(RuntimeError):
        platform.record_resource(
            ResourcePlan(
                "blocked", profile.id, scope.tenant, scope.workspace, cpu=1
            ),
            scope,
        )
    platform.release_kill_switch(profile.id, scope)


def test_resources_performance_cost_latency_capacity(platform, scope, profile):
    platform.record_resource(
        ResourcePlan(
            "resource-1",
            profile.id,
            scope.tenant,
            scope.workspace,
            2,
            4,
            10,
            1,
            1,
            5,
            8,
        ),
        scope,
    )
    platform.record_performance(
        PerformanceRecord(
            "performance-1",
            profile.id,
            scope.tenant,
            scope.workspace,
            100,
            0.2,
            0.7,
            0.9,
            ("queue",),
            {"throughput": 0.1},
        ),
        scope,
    )
    platform.record_cost(
        CostRecord(
            "cost-1",
            profile.id,
            scope.tenant,
            scope.workspace,
            10,
            2,
            1,
            1,
            20,
            6,
        ),
        scope,
    )
    platform.record_latency(
        LatencyRecord(
            "latency-1",
            profile.id,
            scope.tenant,
            scope.workspace,
            0.1,
            0.2,
            0.3,
            0.4,
            ("cache",),
        ),
        scope,
    )
    platform.plan_capacity(
        CapacityPlan(
            "capacity-1",
            profile.id,
            scope.tenant,
            scope.workspace,
            1000,
            "scale-out",
            0.8,
            {"min": 2, "max": 10},
            200,
        ),
        scope,
    )
    dashboard = platform.dashboard(scope)
    assert all(
        dashboard[name]
        for name in ("resources", "performance", "cost", "latency", "capacity")
    )
    with pytest.raises(ValueError):
        platform.record_latency(
            LatencyRecord(
                "bad",
                profile.id,
                scope.tenant,
                scope.workspace,
                1,
                0.8,
                0.9,
                1.1,
            ),
            scope,
        )


def test_experiments_recommendations_evaluation_monitoring(
    platform, scope, profile
):
    platform.experiment(
        Experiment(
            "experiment-1",
            profile.id,
            scope.tenant,
            scope.workspace,
            "canary",
            ApprovalState.APPROVED,
            "checkpoint://1",
            {"gain": 0.2},
        ),
        scope,
    )
    platform.recommend(
        Recommendation(
            "recommendation-1",
            profile.id,
            scope.tenant,
            scope.workspace,
            "high",
            10,
            0.2,
            0.9,
            ("simulate", "approve", "canary"),
        ),
        scope,
    )
    platform.evaluate(
        Evaluation(
            "evaluation-1",
            profile.id,
            scope.tenant,
            scope.workspace,
            {"throughput": 100},
            {"regression": 0},
            {"quality": 0.95},
            0.2,
            0.9,
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
            1,
            (),
            {"cpu": 0.5},
            {"throughput": 0.1},
        ),
        scope,
    )
    assert platform.dashboard(scope)["monitoring"]["health"] == "healthy"
    with pytest.raises(PermissionError):
        platform.recommend(
            Recommendation(
                "risky",
                profile.id,
                scope.tenant,
                scope.workspace,
                "high",
                100,
                0.8,
                0.9,
                ("execute",),
            ),
            scope,
        )


def test_governance_requires_approval_and_rollback(platform, scope, profile):
    with pytest.raises(PermissionError):
        platform.optimize(
            OptimizationCycle(
                "denied",
                profile.id,
                scope.tenant,
                scope.workspace,
                StrategyType.PREDICTIVE,
            ),
            scope,
        )
    with pytest.raises(PermissionError):
        platform.experiment(
            Experiment(
                "unsafe",
                profile.id,
                scope.tenant,
                scope.workspace,
                "shadow",
                ApprovalState.PENDING,
                "",
            ),
            scope,
        )
