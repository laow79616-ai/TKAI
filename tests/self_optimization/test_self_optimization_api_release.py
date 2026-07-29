from pathlib import Path

from self_optimization import OptimizationScope, SelfOptimizationPlatform
from self_optimization.api import (
    SelfOptimizationAPI,
    register_self_optimization_routes,
)
from self_optimization.dashboard import SECTIONS
from self_optimization.metrics import METRICS


class FakeApp:
    def __init__(self):
        self.routes = []

    def add_api_route(self, path, endpoint, methods, tags):
        self.routes.append((path, endpoint, methods, tags))


def test_api_dashboard_and_metrics_contract():
    platform = SelfOptimizationPlatform()
    app = FakeApp()
    register_self_optimization_routes(app, platform)
    paths = {route[0] for route in app.routes}
    assert set(SelfOptimizationAPI.ROUTES) <= paths
    assert "/self-optimization/metrics" in paths
    scope = OptimizationScope("tenant", "workspace", "api")
    assert SelfOptimizationAPI(platform).get("/self-optimization/profiles", scope) == []
    assert set(SECTIONS) <= platform.dashboard(scope).keys()
    assert all(name in platform.metrics.render_prometheus() for name in METRICS)


def test_structure_documentation_packaging_and_regression():
    root = Path(__file__).parents[2]
    modules = (
        "profiles",
        "optimization",
        "strategies",
        "resource_management",
        "performance",
        "cost",
        "latency",
        "capacity",
        "experiments",
        "recommendations",
        "feedback",
        "evaluation",
        "governance",
        "safety",
        "monitoring",
        "dashboard",
        "api",
    )
    assert all(
        (root / "self_optimization" / name / "__init__.py").is_file()
        for name in modules
    )
    documents = (
        "Architecture",
        "Lifecycle",
        "Optimization",
        "Strategies",
        "Performance",
        "Cost",
        "Latency",
        "Capacity",
        "Experiments",
        "Recommendations",
        "Safety",
        "Governance",
        "OperationsGuide",
    )
    assert all(
        (root / "docs" / "self_optimization" / f"{name}.md").is_file()
        for name in documents
    )
    assert "self_optimization*" in (root / "pyproject.toml").read_text("utf-8")
    preserved = (
        "self_evolving",
        "autonomous_intelligence",
        "cognitive_architecture",
        "multi_agent",
        "autonomous_operations",
        "knowledge_graph",
        "command_center",
        "business_intelligence",
        "decision_intelligence",
        "digital_twin",
        "integration_hub",
        "event_streaming",
        "api_management",
        "integration_platform",
        "automation_platform",
        "operations_platform",
        "security_platform",
        "model_platform",
        "data_platform",
        "governance",
        "collaboration",
        "reasoning_engine",
        "memory_engine",
        "orchestrator",
        "app_store",
        "workflow_platform",
        "knowledge_platform",
        "applications",
        "enterprise",
        "cloud",
        "studio",
        "marketplace",
    )
    assert all((root / name).is_dir() for name in preserved)
