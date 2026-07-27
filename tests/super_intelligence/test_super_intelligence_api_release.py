from pathlib import Path

from super_intelligence import IntelligenceScope, SuperIntelligencePlatform
from super_intelligence.api import (
    SuperIntelligenceAPI,
    register_super_intelligence_routes,
)
from super_intelligence.dashboard import SECTIONS
from super_intelligence.metrics import METRICS


class FakeApp:
    def __init__(self) -> None:
        self.routes: list[tuple[object, ...]] = []

    def add_api_route(self, path, endpoint, methods, tags) -> None:
        self.routes.append((path, endpoint, methods, tags))


def test_api_dashboard_and_metrics_contract() -> None:
    platform = SuperIntelligencePlatform()
    app = FakeApp()
    register_super_intelligence_routes(app, platform)
    assert set(SuperIntelligenceAPI.ROUTES) <= {item[0] for item in app.routes}
    assert set(SECTIONS) == {
        "profiles",
        "capabilities",
        "reasoning",
        "planning",
        "knowledge",
        "prediction",
        "optimization",
        "coordination",
        "alignment",
        "evaluation",
        "monitoring",
    }
    scope = IntelligenceScope("tenant", "workspace", "api")
    assert (
        SuperIntelligenceAPI(platform).get("/super-intelligence/profiles", scope) == []
    )
    assert all(name in platform.metrics.render_prometheus() for name in METRICS)


def test_release_structure_docs_packaging_deployment_and_preservation() -> None:
    root = Path(__file__).parents[2]
    modules = (
        "profiles",
        "capabilities",
        "collective_reasoning",
        "strategic_planning",
        "world_models",
        "knowledge_synthesis",
        "prediction",
        "optimization",
        "coordination",
        "decision",
        "adaptation",
        "self_improvement",
        "alignment",
        "governance",
        "evaluation",
        "monitoring",
        "dashboard",
        "api",
    )
    assert all(
        (root / "super_intelligence" / name / "__init__.py").is_file()
        for name in modules
    )
    documents = (
        "Architecture",
        "Lifecycle",
        "Capabilities",
        "CollectiveReasoning",
        "StrategicPlanning",
        "WorldModels",
        "KnowledgeSynthesis",
        "Prediction",
        "Optimization",
        "Coordination",
        "Decision",
        "Alignment",
        "Evaluation",
        "Security",
        "OperationsGuide",
    )
    assert all(
        (root / "docs" / "super_intelligence" / f"{name}.md").is_file()
        for name in documents
    )
    assert "super_intelligence*" in (root / "pyproject.toml").read_text("utf-8")
    assert (root / "Dockerfile.api").is_file()
    assert (root / "deployment" / "helm" / "tkai").is_dir()
    assert (root / ".github" / "workflows").is_dir()
    preserved = (
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
