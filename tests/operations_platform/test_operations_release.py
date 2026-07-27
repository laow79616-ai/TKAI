from pathlib import Path


def test_packaging_documentation_deployment_release_and_regression() -> None:
    root = Path(__file__).resolve().parents[2]
    required_modules = (
        "monitoring",
        "operations",
        "health",
        "maintenance",
        "backup",
        "restore",
        "capacity",
        "scheduler",
        "jobs",
        "automation",
        "diagnostics",
        "logs",
        "events",
        "notifications",
        "reporting",
        "dashboard",
        "api",
    )
    for module in required_modules:
        assert (root / "operations_platform" / module / "__init__.py").is_file()
    for name in (
        "Architecture",
        "Operations",
        "Health",
        "Backup",
        "Restore",
        "Capacity",
        "Automation",
        "Diagnostics",
        "Security",
    ):
        assert (root / "docs" / "operations_platform" / f"{name}.md").is_file()
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "operations_platform*" in pyproject
    assert (root / "Dockerfile.api").is_file()
    assert (root / "Dockerfile.dashboard").is_file()
    assert (root / "deployment" / "helm" / "tkai").is_dir()
    assert (root / ".github" / "workflows").is_dir()
    for preserved in (
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
