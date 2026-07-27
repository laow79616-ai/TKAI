from pathlib import Path


def test_packaging_docs_deployment_release_and_preserved_platforms() -> None:
    root = Path(__file__).resolve().parents[2]
    modules = (
        "automation",
        "rules",
        "triggers",
        "events",
        "actions",
        "pipelines",
        "scheduler",
        "timers",
        "conditions",
        "policies",
        "approvals",
        "rollback",
        "history",
        "audit",
        "dashboard",
        "api",
    )
    for module in modules:
        assert (root / "automation_platform" / module / "__init__.py").is_file()
    for name in (
        "Architecture",
        "Automation",
        "Triggers",
        "Pipelines",
        "Rollback",
        "Security",
    ):
        assert (root / "docs" / "automation_platform" / f"{name}.md").is_file()
    assert "automation_platform*" in (root / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert (root / "Dockerfile.api").is_file()
    assert (root / "deployment" / "helm" / "tkai").is_dir()
    assert (root / ".github" / "workflows").is_dir()
    for preserved in (
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
