from pathlib import Path

from autonomous_intelligence import (
    AutonomousIntelligencePlatform,
    IntelligenceScope,
)
from autonomous_intelligence.api import (
    AutonomousIntelligenceAPI,
    register_autonomous_intelligence_routes,
)
from autonomous_intelligence.dashboard import SECTIONS
from autonomous_intelligence.metrics import METRICS


class FakeApp:
    def __init__(self):
        self.routes = []

    def add_api_route(self, path, endpoint, methods, tags):
        self.routes.append((path, endpoint, methods, tags))


def test_api_dashboard_metrics_and_validation_contract():
    platform = AutonomousIntelligencePlatform()
    app = FakeApp()
    register_autonomous_intelligence_routes(app, platform)
    paths = {item[0] for item in app.routes}
    assert set(AutonomousIntelligenceAPI.ROUTES) <= paths
    assert set(SECTIONS) == {
        "intelligence",
        "awareness",
        "goals",
        "planning",
        "prediction",
        "learning",
        "reflection",
        "adaptation",
        "execution",
        "monitoring",
    }
    scope = IntelligenceScope("tenant", "workspace", "api")
    assert (
        AutonomousIntelligenceAPI(platform).get(
            "/autonomous-intelligence/profiles", scope
        )
        == []
    )
    assert all(name in platform.metrics.render_prometheus() for name in METRICS)


def test_release_structure_documentation_packaging_and_regression():
    root = Path(__file__).parents[2]
    modules = (
        "intelligence",
        "awareness",
        "intent",
        "goals",
        "reasoning",
        "planning",
        "prediction",
        "learning",
        "reflection",
        "adaptation",
        "execution",
        "coordination",
        "governance",
        "monitoring",
        "dashboard",
        "api",
    )
    assert all(
        (root / "autonomous_intelligence" / name / "__init__.py").is_file()
        for name in modules
    )
    documents = (
        "Architecture",
        "Lifecycle",
        "Awareness",
        "Intent",
        "Goals",
        "Reasoning",
        "Planning",
        "Prediction",
        "Learning",
        "Reflection",
        "Adaptation",
        "Execution",
        "Coordination",
        "Security",
        "OperationsGuide",
    )
    assert all(
        (root / "docs" / "autonomous_intelligence" / f"{name}.md").is_file()
        for name in documents
    )
    assert "autonomous_intelligence*" in (root / "pyproject.toml").read_text("utf-8")
    preserved = (
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
