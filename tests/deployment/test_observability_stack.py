"""Offline regression tests for the optional observability deployment."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from server.api.prometheus import render_prometheus
from server.production import InMemoryMetrics

ROOT = Path(__file__).parents[2]
OBSERVABILITY = ROOT / "deployment" / "observability"
EXPECTED_SERVICES = {
    "prometheus",
    "grafana",
    "loki",
    "alloy",
    "alertmanager",
    "postgres-exporter",
    "nginx-exporter",
}


def _yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_observability_override_has_expected_optional_services() -> None:
    base = _yaml(ROOT / "docker-compose.yml")
    override = _yaml(ROOT / "docker-compose.observability.yml")

    assert list(base["services"]) == ["postgres", "api", "dashboard", "nginx"]
    assert set(override["services"]) == EXPECTED_SERVICES
    assert override["networks"]["observability"]["internal"] is True


def test_prometheus_scrapes_only_supported_targets_and_loads_rules() -> None:
    config = _yaml(OBSERVABILITY / "prometheus" / "prometheus.yml")
    jobs = {
        item["job_name"]: item
        for item in config["scrape_configs"]
    }

    assert set(jobs) == {"prometheus", "api", "postgres", "nginx"}
    assert jobs["api"]["metrics_path"] == "/metrics"
    assert jobs["api"]["static_configs"][0]["targets"] == ["api:8000"]
    assert jobs["postgres"]["static_configs"][0]["targets"] == [
        "postgres-exporter:9187"
    ]
    assert jobs["nginx"]["static_configs"][0]["targets"] == [
        "nginx-exporter:9113"
    ]
    assert config["rule_files"] == ["/etc/prometheus/alerts.yml"]


def test_alerts_cover_availability_targets_and_supported_5xx_metric() -> None:
    rules = _yaml(OBSERVABILITY / "prometheus" / "alerts.yml")
    alerts = {
        rule["alert"]: rule
        for group in rules["groups"]
        for rule in group["rules"]
    }

    assert {
        "TKAIAPIUnavailable",
        "TKAIPostgreSQLUnavailable",
        "TKAINginxUnavailable",
        "PrometheusTargetDown",
        "TKAIAPIElevated5xxRate",
    }.issubset(alerts)
    assert "tkai_http_responses_total" in alerts["TKAIAPIElevated5xxRate"]["expr"]
    assert not any("latency" in item.lower() for item in alerts)

    alertmanager = _yaml(
        OBSERVABILITY / "alertmanager" / "alertmanager.yml"
    )
    assert alertmanager["route"]["receiver"] == "local"
    assert alertmanager["receivers"] == [{"name": "local"}]


def test_grafana_provisions_both_sources_and_complete_overview() -> None:
    datasources = _yaml(
        OBSERVABILITY
        / "grafana"
        / "provisioning"
        / "datasources"
        / "datasources.yml"
    )
    assert {
        (source["name"], source["url"])
        for source in datasources["datasources"]
    } == {
        ("Prometheus", "http://prometheus:9090"),
        ("Loki", "http://loki:3100"),
    }

    dashboard = json.loads(
        (OBSERVABILITY / "grafana" / "dashboards" / "tkai-overview.json").read_text(
            encoding="utf-8"
        )
    )
    titles = {panel["title"] for panel in dashboard["panels"]}
    assert {
        "Service availability",
        "API request rate",
        "API latency",
        "API error rate",
        "PostgreSQL health",
        "Nginx health",
        "Prometheus target health",
    }.issubset(titles)
    latency = next(
        panel for panel in dashboard["panels"] if panel["title"] == "API latency"
    )
    assert latency["type"] == "text"
    assert "no latency histogram" in latency["description"]


def test_loki_retention_and_alloy_log_scope_are_explicit() -> None:
    loki = (OBSERVABILITY / "loki" / "config.yml").read_text(encoding="utf-8")
    alloy = (OBSERVABILITY / "alloy" / "config.alloy").read_text(encoding="utf-8")

    assert "retention_enabled: true" in loki
    assert "retention_period: ${LOKI_RETENTION}" in loki
    assert "schema: v13" in loki
    assert "(api|nginx|postgres|dashboard)" in alloy
    assert "docker.sock" in alloy
    for sensitive in ("password", "secret", "token"):
        assert f'target_label  = "{sensitive}"' not in alloy


def test_monitoring_ports_are_localhost_only_and_credentials_are_external() -> None:
    compose = _yaml(ROOT / "docker-compose.observability.yml")
    services = compose["services"]
    published = {
        name: port
        for name, service in services.items()
        for port in service.get("ports", [])
    }
    assert published
    assert all(str(port).startswith("127.0.0.1:") for port in published.values())

    grafana_environment = services["grafana"]["environment"]
    assert grafana_environment["GF_SECURITY_ADMIN_USER"].startswith(
        "${GRAFANA_ADMIN_USER:"
    )
    assert grafana_environment["GF_SECURITY_ADMIN_PASSWORD"].startswith(
        "${GRAFANA_ADMIN_PASSWORD:"
    )
    compose_text = (ROOT / "docker-compose.observability.yml").read_text(
        encoding="utf-8"
    )
    assert "GF_SECURITY_ADMIN_PASSWORD: admin" not in compose_text


def test_every_observability_healthcheck_uses_a_valid_compose_mode() -> None:
    compose = _yaml(ROOT / "docker-compose.observability.yml")
    valid_modes = {"CMD", "CMD-SHELL", "NONE"}

    healthchecks = [
        service["healthcheck"]["test"]
        for service in compose["services"].values()
        if "healthcheck" in service
    ]
    assert healthchecks
    assert all(test[0] in valid_modes for test in healthchecks)


def test_api_prometheus_exposition_uses_existing_count_metrics() -> None:
    metrics = InMemoryMetrics()
    metrics.increment("http.requests", 2)
    metrics.increment("http.status.200")
    metrics.increment("http.status.503")
    output = render_prometheus(metrics.snapshot())

    assert "tkai_http_requests_total 2" in output
    assert 'tkai_http_responses_total{status="200"} 1' in output
    assert 'tkai_http_responses_total{status="503"} 1' in output
    assert "latency" not in output
