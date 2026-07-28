from pathlib import Path

from cognitive_architecture import CognitiveArchitecturePlatform, CognitiveScope
from cognitive_architecture.api import CognitiveAPI, register_cognitive_routes
from cognitive_architecture.dashboard import SECTIONS
from cognitive_architecture.metrics import METRICS


class FakeApp:
    def __init__(self):
        self.routes = []

    def add_api_route(self, path, endpoint, methods, tags):
        self.routes.append((path, endpoint, methods, tags))


def test_api_dashboard_and_metrics_contract():
    platform = CognitiveArchitecturePlatform()
    app = FakeApp()
    register_cognitive_routes(app, platform)
    paths = {item[0] for item in app.routes}
    assert set(CognitiveAPI.ROUTES) <= paths
    assert set(SECTIONS) == {
        "perception",
        "attention",
        "memory",
        "reasoning",
        "planning",
        "learning",
        "reflection",
        "decision",
        "adaptation",
        "health",
    }
    assert (
        CognitiveAPI(platform).get(
            "/cognitive/models", CognitiveScope("tenant", "workspace", "api")
        )
        == []
    )
    rendered = platform.metrics.render_prometheus()
    assert all(name in rendered for name in METRICS)


def test_release_structure_documentation_and_packaging():
    root = Path(__file__).parents[2]
    modules = (
        "perception",
        "attention",
        "working_memory",
        "long_term_memory",
        "reasoning",
        "planning",
        "learning",
        "reflection",
        "goal_management",
        "decision",
        "execution",
        "adaptation",
        "self_monitoring",
        "metacognition",
        "knowledge",
        "dashboard",
        "api",
    )
    assert all(
        (root / "cognitive_architecture" / name / "__init__.py").is_file()
        for name in modules
    )
    documents = (
        "Architecture",
        "Lifecycle",
        "Perception",
        "Attention",
        "Memory",
        "Reasoning",
        "Planning",
        "Learning",
        "Reflection",
        "Decision",
        "Adaptation",
        "Metacognition",
        "Security",
        "OperationsGuide",
    )
    assert all(
        (root / "docs" / "cognitive_architecture" / f"{name}.md").is_file()
        for name in documents
    )
    assert "cognitive_architecture*" in (root / "pyproject.toml").read_text("utf-8")
