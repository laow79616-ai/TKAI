from pathlib import Path

from command_center import METRICS, CommandCenterMetrics


def test_release_structure_documentation_metrics_and_frontend() -> None:
    root = Path(__file__).parents[2]
    modules = (
        "overview",
        "control_planes",
        "workspaces",
        "tenants",
        "agents",
        "automation",
        "operations",
        "alerts",
        "incidents",
        "tasks",
        "playbooks",
        "health",
        "topology",
        "live_status",
        "activity",
        "audit",
        "dashboard",
        "api",
    )
    for module in modules:
        assert (root / "command_center" / module / "__init__.py").is_file()
    for document in (
        "Architecture",
        "ControlPlane",
        "Operations",
        "Alerts",
        "Incidents",
        "Tasks",
        "Playbooks",
        "Topology",
        "Health",
        "Dashboard",
        "Security",
        "OperationsGuide",
    ):
        assert (root / "docs" / "command_center" / f"{document}.md").is_file()
    assert len(METRICS) == 8
    rendered = CommandCenterMetrics().render_prometheus()
    assert "command_center_instances_total 0" in rendered
    assert "command_center*" in (root / "pyproject.toml").read_text("utf-8")
    app = (root / "dashboard" / "frontend" / "src" / "App.tsx").read_text("utf-8")
    assert "CommandCenterPage" in app
    server = (root / "server" / "api" / "app.py").read_text("utf-8")
    assert "register_command_center_routes" in server
