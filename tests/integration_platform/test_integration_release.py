from pathlib import Path


def test_packaging_docs_deployment_release_and_preserved_platforms() -> None:
    root = Path(__file__).resolve().parents[2]
    modules = (
        "integrations",
        "connectors",
        "credentials",
        "webhooks",
        "apis",
        "events",
        "messaging",
        "databases",
        "storage",
        "saas",
        "erp",
        "crm",
        "collaboration",
        "monitoring",
        "retries",
        "dead_letter",
        "dashboard",
        "api",
    )
    for module in modules:
        assert (root / "integration_platform" / module / "__init__.py").is_file()
    for name in (
        "Architecture",
        "ConnectorLifecycle",
        "Credentials",
        "APIIntegration",
        "Webhooks",
        "Events",
        "Messaging",
        "Databases",
        "Storage",
        "Reliability",
        "Security",
        "Operations",
    ):
        assert (root / "docs" / "integration_platform" / f"{name}.md").is_file()
    assert "integration_platform*" in (root / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert (root / "Dockerfile.api").is_file()
    assert (root / "deployment" / "helm" / "tkai").is_dir()
    assert (root / ".github" / "workflows").is_dir()
    for preserved in (
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
    ):
        assert (root / preserved).is_dir()
