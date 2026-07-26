from pathlib import Path


def test_collaboration_is_packaged_for_docker_and_kubernetes_runtime() -> None:
    root = Path(__file__).parents[2]
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    manifest = (root / "MANIFEST.in").read_text(encoding="utf-8")
    dockerfile = (root / "Dockerfile.api").read_text(encoding="utf-8")
    chart = (root / "deployment/helm/tkai/Chart.yaml").read_text(encoding="utf-8")
    assert '"collaboration*"' in pyproject
    assert "recursive-include collaboration" in manifest
    assert "pip install" in dockerfile
    assert "apiVersion:" in chart
