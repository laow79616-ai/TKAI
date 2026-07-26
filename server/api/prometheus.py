"""Prometheus exposition for the request counters already kept by the API."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any

from applications.runtime import ApplicationMetrics
from knowledge_platform.metrics import KnowledgeMetrics
from marketplace.enterprise_store import MarketplaceMetrics
from server.production import MetricsSnapshot, ProductionRuntime
from tkai.agent import AgentMetrics
from tkai.plugins.marketplace import PluginMetrics
from workflow_platform.metrics import WorkflowMetrics


def render_prometheus(snapshot: MetricsSnapshot) -> str:
    """Render the existing count-only runtime metrics in Prometheus text format."""
    counters = snapshot.to_dict()
    lines = [
        "# HELP tkai_http_requests_total Total HTTP requests handled by the API.",
        "# TYPE tkai_http_requests_total counter",
        f"tkai_http_requests_total {counters.get('http.requests', 0)}",
        "# HELP tkai_http_responses_total HTTP responses by status code.",
        "# TYPE tkai_http_responses_total counter",
    ]
    for name, value in sorted(counters.items()):
        if not name.startswith("http.status."):
            continue
        status = name.removeprefix("http.status.")
        if status.isdigit():
            lines.append(f'tkai_http_responses_total{{status="{status}"}} {value}')
    return "\n".join(lines) + "\n"


def prometheus_endpoint(
    runtime: ProductionRuntime,
    agent_metrics: AgentMetrics | None = None,
    plugin_metrics: PluginMetrics | None = None,
    marketplace_metrics: MarketplaceMetrics | None = None,
    application_metrics: ApplicationMetrics | None = None,
    knowledge_metrics: KnowledgeMetrics | None = None,
    workflow_metrics: WorkflowMetrics | None = None,
) -> Callable[[], Any]:
    """Create a FastAPI endpoint without making FastAPI a core dependency."""

    def endpoint() -> Any:
        response_type = import_module("fastapi.responses").PlainTextResponse
        body = render_prometheus(runtime.metrics.snapshot())
        if agent_metrics is not None:
            body += agent_metrics.render_prometheus()
        if plugin_metrics is not None:
            body += plugin_metrics.render_prometheus()
        if marketplace_metrics is not None:
            body += marketplace_metrics.render_prometheus()
        if application_metrics is not None:
            body += application_metrics.render_prometheus()
        if knowledge_metrics is not None:
            body += knowledge_metrics.render_prometheus()
        if workflow_metrics is not None:
            body += workflow_metrics.render_prometheus()
        return response_type(
            body,
            media_type="text/plain; version=0.0.4",
        )

    return endpoint
