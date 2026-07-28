from pathlib import Path


def test_data_platform_packaging_deployment_and_release() -> None:
    root = Path(__file__).parents[2]
    assert '"data_platform*"' in (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "recursive-include data_platform" in (root / "MANIFEST.in").read_text(
        encoding="utf-8"
    )
    assert "DataPlatform" in (root / "server/api/app.py").read_text(encoding="utf-8")
    architecture = (root / "docs/data-platform/Architecture.md").read_text(
        encoding="utf-8"
    )
    for preserved in (
        "AI Governance Platform",
        "AI Collaboration Platform",
        "AI Reasoning Engine",
        "AI Memory Engine",
        "AI Orchestrator",
        "Enterprise App Store",
        "Enterprise Workflow Platform",
        "Enterprise Knowledge Platform",
        "AI Application Center",
        "Enterprise Agent Runtime",
        "Plugin Marketplace",
        "Enterprise Platform",
        "Cloud Native",
        "AI Studio",
        "Enterprise Marketplace",
        "Docker",
        "Kubernetes",
        "CI/CD",
        "Observability",
    ):
        assert preserved in architecture
    for name in (
        "Architecture",
        "Pipelines",
        "Quality",
        "Lineage",
        "Schema",
        "Classification",
        "Security",
    ):
        assert (root / f"docs/data-platform/{name}.md").is_file()
    for name in (
        "catalog",
        "datasets",
        "pipelines",
        "storage",
        "lineage",
        "quality",
        "classification",
        "governance",
        "schemas",
        "transform",
        "validation",
        "connectors",
        "imports",
        "exports",
        "versions",
        "retention",
        "dashboard",
        "api",
    ):
        assert (root / f"data_platform/{name}").is_dir()
