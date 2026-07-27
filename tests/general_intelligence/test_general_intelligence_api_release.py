from pathlib import Path

from general_intelligence import (
    GeneralIntelligencePlatform,
    IntelligenceScope,
)
from general_intelligence.api import (
    GeneralIntelligenceAPI,
    register_general_intelligence_routes,
)
from general_intelligence.dashboard import SECTIONS
from general_intelligence.metrics import METRICS


class FakeApp:
    def __init__(self):
        self.routes = []

    def add_api_route(self, path, endpoint, methods, tags):
        self.routes.append((path, endpoint, methods, tags))


def test_api_dashboard_metrics_and_validation_contract():
    platform = GeneralIntelligencePlatform()
    app = FakeApp()
    register_general_intelligence_routes(app, platform)
    paths = {item[0] for item in app.routes}
    assert set(GeneralIntelligenceAPI.ROUTES) <= paths
    assert set(SECTIONS) == {
        "profiles",
        "capabilities",
        "knowledge",
        "reasoning",
        "planning",
        "learning",
        "execution",
        "reflection",
        "evaluation",
        "monitoring",
    }
    scope = IntelligenceScope("tenant", "workspace", "api")
    assert (
        GeneralIntelligenceAPI(platform).get(
            "/general-intelligence/profiles", scope
        )
        == []
    )
    assert all(name in platform.metrics.render_prometheus() for name in METRICS)


def test_release_structure_documentation_packaging_and_regression():
    root = Path(__file__).parents[2]
    modules = (
        "profiles",
        "capabilities",
        "knowledge",
        "goals",
        "reasoning",
        "planning",
        "learning",
        "memory",
        "perception",
        "reflection",
        "adaptation",
        "execution",
        "governance",
        "evaluation",
        "monitoring",
        "dashboard",
        "api",
    )
    assert all(
        (root / "general_intelligence" / name / "__init__.py").is_file()
        for name in modules
    )
    documents = (
        "Architecture",
        "Lifecycle",
        "Capabilities",
        "Knowledge",
        "Reasoning",
        "Planning",
        "Learning",
        "Memory",
        "Perception",
        "Reflection",
        "Adaptation",
        "Execution",
        "Evaluation",
        "Security",
        "OperationsGuide",
    )
    assert all(
        (root / "docs" / "general_intelligence" / f"{name}.md").is_file()
        for name in documents
    )
    assert "general_intelligence*" in (root / "pyproject.toml").read_text("utf-8")
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
