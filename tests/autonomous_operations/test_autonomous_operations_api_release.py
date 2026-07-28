from autonomous_operations import AutonomousOperationsPlatform
from autonomous_operations.api import register_autonomous_operations_routes
from autonomous_operations.dashboard import SECTIONS
from autonomous_operations.metrics import METRICS


class FakeApp:
    def __init__(self):
        self.routes = []

    def add_api_route(self, path, endpoint, methods, tags):
        self.routes.append((path, endpoint, methods, tags))


def test_api_dashboard_metrics_and_package_contract():
    app = FakeApp()
    platform = AutonomousOperationsPlatform()
    register_autonomous_operations_routes(app, platform)
    paths = {route[0] for route in app.routes}
    assert {
        "/autonomous-operations",
        "/autonomous-operations/objectives",
        "/autonomous-operations/policies",
        "/autonomous-operations/strategies",
        "/autonomous-operations/executions",
        "/autonomous-operations/feedback",
        "/autonomous-operations/optimization",
        "/autonomous-operations/learning",
        "/autonomous-operations/safety",
    } <= paths
    assert set(SECTIONS) == {
        "operations",
        "objectives",
        "policies",
        "strategies",
        "executions",
        "feedback",
        "optimization",
        "learning",
        "safety",
    }
    rendered = platform.metrics.render_prometheus()
    assert all(name in rendered for name in METRICS)
