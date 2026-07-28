from pathlib import Path

from self_evolving import EvolutionScope, SelfEvolvingPlatform
from self_evolving.api import SelfEvolvingAPI, register_self_evolving_routes
from self_evolving.dashboard import SECTIONS
from self_evolving.metrics import METRICS


class FakeApp:
    def __init__(self):
        self.routes = []

    def add_api_route(self, path, endpoint, methods, tags):
        self.routes.append((path, endpoint, methods, tags))


def test_api_dashboard_and_metrics_contract():
    platform = SelfEvolvingPlatform()
    app = FakeApp()
    register_self_evolving_routes(app, platform)
    paths = {route[0] for route in app.routes}
    assert set(SelfEvolvingAPI.ROUTES) <= paths
    assert "/self-evolving/metrics" in paths
    scope = EvolutionScope("tenant", "workspace", "api")
    assert SelfEvolvingAPI(platform).get("/self-evolving/profiles", scope) == []
    assert set(SECTIONS) <= platform.dashboard(scope).keys()
    assert all(name in platform.metrics.render_prometheus() for name in METRICS)


def test_release_structure_documentation_packaging_and_regression():
    root = Path(__file__).parents[2]
    modules = (
        "profiles",
        "evolution",
        "learning",
        "adaptation",
        "mutation",
        "evaluation",
        "experiments",
        "optimization",
        "feedback",
        "knowledge",
        "memory",
        "reasoning",
        "governance",
        "safety",
        "monitoring",
        "dashboard",
        "api",
    )
    assert all(
        (root / "self_evolving" / name / "__init__.py").is_file() for name in modules
    )
    documents = (
        "Architecture",
        "Lifecycle",
        "Evolution",
        "Learning",
        "Adaptation",
        "Mutation",
        "Experiments",
        "Optimization",
        "Safety",
        "Governance",
        "OperationsGuide",
    )
    assert all(
        (root / "docs" / "self_evolving" / f"{name}.md").is_file() for name in documents
    )
    assert "self_evolving*" in (root / "pyproject.toml").read_text("utf-8")
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
