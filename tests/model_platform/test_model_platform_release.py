from pathlib import Path


def test_model_platform_packaging_deployment_dashboard_and_release() -> None:
    root = Path(__file__).parents[2]
    assert '"model_platform*"' in (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "recursive-include model_platform" in (root / "MANIFEST.in").read_text(
        encoding="utf-8"
    )
    app = (root / "server/api/app.py").read_text(encoding="utf-8")
    assert "ModelPlatform" in app and "register_model_routes" in app
    prometheus = (root / "server/api/prometheus.py").read_text(encoding="utf-8")
    assert "model_metrics.render_prometheus()" in prometheus
    frontend = (root / "dashboard/frontend/src/App.tsx").read_text(encoding="utf-8")
    assert "model-providers" in frontend and "model-governance" in frontend

    architecture = (root / "docs/model-platform/Architecture.md").read_text(
        encoding="utf-8"
    )
    for preserved in (
        "Enterprise AI Data Platform",
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
        "Providers",
        "Profiles",
        "Routing",
        "Fallback",
        "Deployment",
        "Evaluation",
        "Benchmarks",
        "Quota",
        "Cost",
        "Security",
        "Governance",
    ):
        assert (root / f"docs/model-platform/{name}.md").is_file()
    for name in (
        "registry",
        "providers",
        "models",
        "profiles",
        "versions",
        "deployment",
        "routing",
        "fallback",
        "evaluation",
        "benchmarks",
        "quotas",
        "usage",
        "cost",
        "security",
        "governance",
        "dashboard",
        "api",
    ):
        assert (root / f"model_platform/{name}").is_dir()
