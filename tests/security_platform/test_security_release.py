from pathlib import Path


def test_packaging_documentation_deployment_and_release_regression() -> None:
    root = Path(__file__).resolve().parents[2]
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    app = (root / "server/api/app.py").read_text(encoding="utf-8")
    prometheus = (root / "server/api/prometheus.py").read_text(encoding="utf-8")
    assert "security_platform*" in pyproject
    assert "register_security_routes" in app
    assert "security_platform.metrics" in app
    assert "SecurityMetrics" in prometheus
    for name in (
        "Architecture",
        "Identity",
        "Authentication",
        "Authorization",
        "Secrets",
        "Encryption",
        "IncidentResponse",
        "Compliance",
    ):
        assert (root / "docs/security" / f"{name}.md").is_file()
    assert (root / "Dockerfile.api").is_file()
    assert (root / "deployment/helm/tkai").is_dir()
