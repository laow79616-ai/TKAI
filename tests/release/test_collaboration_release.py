from pathlib import Path


def test_collaboration_release_documentation_and_preserved_platforms() -> None:
    root = Path(__file__).parents[2]
    architecture = (root / "docs/collaboration/Architecture.md").read_text(
        encoding="utf-8"
    )
    for platform in (
        "Reasoning Engine",
        "Memory Engine",
        "Orchestrator",
        "App Store",
        "Workflow Platform",
        "Knowledge Platform",
        "Application Center",
        "Agent Runtime",
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
        assert platform in architecture
    for name in (
        "Workspace",
        "Project",
        "Session",
        "SharedContext",
        "SharedMemory",
        "Handoff",
        "Security",
    ):
        assert (root / f"docs/collaboration/{name}.md").is_file()
