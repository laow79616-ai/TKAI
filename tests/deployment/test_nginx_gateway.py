"""Offline regression tests for the Nginx HTTP and HTTPS gateway."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]
NGINX = ROOT / "deployment" / "nginx"


def _compose() -> dict[str, object]:
    return yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))


def test_only_gateway_profiles_publish_host_ports() -> None:
    services = _compose()["services"]

    assert "ports" not in services["postgres"]
    assert "ports" not in services["api"]
    assert "ports" not in services["dashboard"]
    assert services["gateway"]["profiles"] == ["development"]
    assert services["gateway-https"]["profiles"] == ["production"]
    assert services["gateway"]["ports"] == ["${HTTP_PORT:-80}:80"]
    assert "${HTTPS_PORT:-443}:443" in services["gateway-https"]["ports"]


def test_gateways_wait_for_upstreams_and_have_health_checks() -> None:
    services = _compose()["services"]

    for name in ("gateway", "gateway-https"):
        service = services[name]
        assert set(service["depends_on"]) == {"api", "dashboard"}
        assert all(
            dependency["condition"] == "service_healthy"
            for dependency in service["depends_on"].values()
        )
        assert "/nginx-health" in " ".join(service["healthcheck"]["test"])


def test_production_gateway_mounts_operator_tls_files_read_only() -> None:
    production = _compose()["services"]["gateway-https"]
    mounts = "\n".join(production["volumes"])

    assert "TLS_CERTIFICATE_PATH" in mounts
    assert "TLS_PRIVATE_KEY_PATH" in mounts
    assert "/etc/nginx/tls/tls.crt:ro" in mounts
    assert "/etc/nginx/tls/tls.key:ro" in mounts


def test_gateway_routes_api_contract_and_dashboard_fallback() -> None:
    common = (NGINX / "gateway-common.conf").read_text(encoding="utf-8")

    for route in (
        "/api/",
        "/docs",
        "/openapi.json",
        "/health",
        "/ready",
        "/live",
        "/metrics",
    ):
        assert f"location {'=' if route != '/api/' else ''} {route}".replace(
            "  ", " "
        ) in common
    assert "proxy_pass http://api:8000/;" in common
    assert "proxy_pass http://dashboard:4173;" in common
    assert "proxy_pass http://api:8000/health/ready;" in common
    assert "proxy_pass http://api:8000/health/live;" in common


def test_gateway_hardening_compression_and_asset_cache_are_configured() -> None:
    common = (NGINX / "gateway-common.conf").read_text(encoding="utf-8")
    headers = (NGINX / "security-headers.conf").read_text(encoding="utf-8")
    https = (NGINX / "https.conf").read_text(encoding="utf-8")

    assert "gzip on;" in common
    assert "max-age=31536000, immutable" in common
    for header in (
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Referrer-Policy",
        "Permissions-Policy",
        "Content-Security-Policy",
    ):
        assert header in headers
    assert "Strict-Transport-Security" in https
    assert "return 301 https://$host$request_uri;" in https
    assert "ssl_protocols TLSv1.2 TLSv1.3;" in https


def test_gateway_environment_and_documentation_cover_both_modes() -> None:
    environment = (ROOT / ".env.example").read_text(encoding="utf-8")
    documentation = (
        ROOT / "docs" / "deployment" / "NginxGateway.md"
    ).read_text(encoding="utf-8")

    for variable in (
        "HTTP_PORT",
        "HTTPS_PORT",
        "TLS_CERTIFICATE_PATH",
        "TLS_PRIVATE_KEY_PATH",
    ):
        assert f"{variable}=" in environment
    assert "--profile development" in documentation
    assert "--profile production" in documentation
