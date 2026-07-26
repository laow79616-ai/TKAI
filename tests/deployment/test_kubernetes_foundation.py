from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CHART = ROOT / "deployment" / "helm" / "tkai"
KUBE = ROOT / "deployment" / "kubernetes"


def read(name: str) -> str:
    return (CHART / name).read_text(encoding="utf-8")


def test_chart_and_static_manifest_structure() -> None:
    chart = yaml.safe_load(read("Chart.yaml"))
    values = yaml.safe_load(read("values.yaml"))
    assert chart["apiVersion"] == "v2"
    assert chart["name"] == "tkai"
    assert values["api"]["replicas"] >= 2
    for name in (
        "namespace",
        "config",
        "secrets",
        "api",
        "dashboard",
        "nginx",
        "postgres",
        "observability",
        "network",
        "rbac",
        "autoscaling",
        "policies",
    ):
        assert (KUBE / name).is_dir()


def test_workloads_have_security_resources_and_three_probes() -> None:
    core = read("templates/core.yaml")
    helpers = read("templates/_helpers.tpl")
    postgres = read("templates/postgresql.yaml")
    assert "kind: Deployment" in core
    assert "kind: StatefulSet" in postgres
    for token in (
        "runAsNonRoot: true",
        "readOnlyRootFilesystem: true",
        'capabilities: {drop: ["ALL"]}',
        "readinessProbe:",
        "livenessProbe:",
        "startupProbe:",
        "resources:",
        "kind: PodDisruptionBudget",
        "RollingUpdate",
        "podAntiAffinity:",
    ):
        assert token in core or token in helpers
    assert "volumeClaimTemplates:" in postgres
    assert "existingSecret" in postgres


def test_rbac_network_policy_hpa_and_ingress_are_bounded() -> None:
    security = read("templates/security.yaml")
    hpa = read("templates/autoscaling.yaml")
    ingress = read("templates/ingress.yaml")
    assert "kind: Role" in security and 'verbs: ["get"]' in security
    assert security.count("kind: NetworkPolicy") == 2
    assert "maxReplicas:" in hpa and "minReplicas:" in hpa
    assert "stabilizationWindowSeconds" in hpa
    assert "tlsSecretName" in ingress
    assert "path: /api" in ingress and "path: /health" in ingress
    assert "path: /metrics" not in ingress


def test_observability_alerts_and_ci_contract() -> None:
    observability = read("templates/observability.yaml")
    workflow = (ROOT / ".github/workflows/kubernetes.yml").read_text(encoding="utf-8")
    for token in (
        "ServiceMonitor",
        "TKAIWorkloadUnavailable",
        "TKAIPodRestarting",
        "TKAIDeploymentReplicaMismatch",
        "prometheus",
        "grafana",
        "loki",
        "alertmanager",
    ):
        assert token in observability
    for token in ("helm lint", "helm template", "hardcoded", "startupProbe"):
        assert token in workflow


def test_no_committed_secret_values() -> None:
    files = list((ROOT / "deployment/helm").rglob("*")) + list(KUBE.rglob("*"))
    content = "\n".join(
        path.read_text(encoding="utf-8") for path in files if path.is_file()
    ).lower()
    forbidden = (
        "password: changeme",
        "password: admin",
        "private key-----",
        "tls.crt:",
    )
    assert not any(token in content for token in forbidden)
