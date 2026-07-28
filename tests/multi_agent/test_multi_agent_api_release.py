from pathlib import Path

from multi_agent import MultiAgentPlatform, MultiAgentScope
from multi_agent.api import MultiAgentAPI, register_multi_agent_routes
from multi_agent.dashboard import SECTIONS
from multi_agent.metrics import METRICS


class FakeApp:
    def __init__(self):
        self.routes = []

    def add_api_route(self, path, endpoint, methods, tags):
        self.routes.append((path, endpoint, methods, tags))


def test_api_dashboard_metrics_contract():
    platform = MultiAgentPlatform()
    app = FakeApp()
    register_multi_agent_routes(app, platform)
    paths = {item[0] for item in app.routes}
    assert set(MultiAgentAPI.ROUTES) <= paths
    assert set(SECTIONS) == {
        "agents",
        "teams",
        "coordination",
        "execution",
        "planning",
        "consensus",
        "negotiation",
        "memory",
        "knowledge",
        "health",
    }
    assert (
        MultiAgentAPI(platform).get(
            "/multi-agent/agents", MultiAgentScope("tenant", "workspace", "api")
        )
        == []
    )
    assert all(name in platform.metrics.render_prometheus() for name in METRICS)


def test_release_structure_and_documentation():
    root = Path(__file__).parents[2]
    modules = (
        "agents",
        "teams",
        "roles",
        "capabilities",
        "coordination",
        "communication",
        "delegation",
        "planning",
        "consensus",
        "negotiation",
        "memory",
        "knowledge",
        "reasoning",
        "execution",
        "monitoring",
        "governance",
        "dashboard",
        "api",
    )
    assert all(
        (root / "multi_agent" / name / "__init__.py").is_file() for name in modules
    )
    documents = (
        "Architecture",
        "AgentLifecycle",
        "Coordination",
        "Planning",
        "Consensus",
        "Negotiation",
        "Execution",
        "Monitoring",
        "Governance",
        "OperationsGuide",
    )
    assert all(
        (root / "docs" / "multi_agent" / f"{name}.md").is_file() for name in documents
    )
    assert "multi_agent*" in (root / "pyproject.toml").read_text("utf-8")
