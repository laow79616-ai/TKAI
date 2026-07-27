from pathlib import Path


def test_structure_docs_deployment_release_frontend_and_preserved_platforms() -> None:
    root = Path(__file__).resolve().parents[2]
    modules = (
        "catalog", "connectors", "instances", "mappings", "flows", "credentials",
        "policies", "health", "retries", "dead_letter", "schedules", "events",
        "versions", "templates", "analytics", "dashboard", "api",
    )
    for module in modules:
        assert (root / "integration_hub" / module / "__init__.py").is_file()
    for name in (
        "Architecture", "ConnectorLifecycle", "Instances", "Mappings", "Flows",
        "Credentials", "Policies", "Health", "Scheduling", "Templates",
        "Analytics", "Security", "Operations",
    ):
        assert (root / "docs" / "integration_hub" / f"{name}.md").is_file()
    assert "integration_hub*" in (root / "pyproject.toml").read_text("utf-8")
    assert "integration-hub" in (
        root / "dashboard" / "frontend" / "src" / "App.tsx"
    ).read_text("utf-8")
    assert (root / "Dockerfile.api").is_file()
    assert (root / "deployment" / "helm" / "tkai").is_dir()
    assert (root / ".github" / "workflows").is_dir()
    for preserved in (
        "event_streaming", "api_management", "integration_platform",
        "automation_platform", "operations_platform", "security_platform",
        "model_platform", "data_platform", "governance", "collaboration",
        "reasoning_engine", "memory_engine", "orchestrator", "app_store",
        "workflow_platform", "knowledge_platform", "applications", "enterprise",
        "cloud", "studio", "marketplace",
    ):
        assert (root / preserved).is_dir()
