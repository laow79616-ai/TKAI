"""Thin CLI adapters for the provider-neutral AI service layer."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, TypeVar

import typer

from tkai.ai import ProviderConfigurationError, ProviderError, ProviderNotFoundError
from tkai.ai.cli_service import AICommandService
from tkai.ai.doctor import DoctorReport

app = typer.Typer(help="Inspect configured AI services without provider internals.")
_service = AICommandService()

T = TypeVar("T")


def _render(value: Any, *, as_json: bool) -> None:
    """Print structured output consistently without leaking implementation objects."""
    if as_json:
        typer.echo(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str))
        return
    if isinstance(value, str):
        typer.echo(value)
        return
    typer.echo(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
    )


def _exit_for_report(report: DoctorReport) -> None:
    """Map diagnostic errors to the documented validation exit code."""
    if report.errors:
        raise typer.Exit(1)


def _call(operation: Callable[[], T]) -> T:
    """Translate expected service failures into concise documented exit codes."""
    try:
        return operation()
    except (ProviderConfigurationError, ProviderNotFoundError, ValueError) as error:
        typer.echo(f"configuration error: {error}", err=True)
        raise typer.Exit(2) from error
    except ProviderError as error:
        typer.echo(f"runtime error: {type(error).__name__}", err=True)
        raise typer.Exit(3) from error
    except RuntimeError as error:
        typer.echo(f"runtime error: {type(error).__name__}", err=True)
        raise typer.Exit(3) from error


@app.command("doctor")
def doctor(
    as_json: bool = typer.Option(False, "--json"),
    text: bool = typer.Option(False, "--text"),
) -> None:
    """Run all read-only AI diagnostics through :class:`DoctorService`."""
    if as_json and text:
        _call(lambda: (_ for _ in ()).throw(ValueError("choose --json or --text")))
    report = _call(_service.doctor)
    typer.echo(report.to_json() if as_json else report.to_text())
    _exit_for_report(report)


@app.command("providers")
def providers(as_json: bool = typer.Option(False, "--json")) -> None:
    """List provider, alias, default, capability, and model-override metadata."""
    value = _call(_service.providers)
    if as_json:
        _render(value, as_json=True)
        return
    if not value:
        typer.echo("No registered providers")
        return
    for item in value:
        aliases = ", ".join(item["aliases"]) or "-"
        capabilities = ", ".join(item["capabilities"]) or "-"
        typer.echo(
            f"{item['provider']} default={item['default']} aliases={aliases} "
            f"capabilities={capabilities} model_count={item['model_count']}"
        )


@app.command("capabilities")
def capabilities(
    provider: str | None = typer.Option(None, "--provider"),
    model: str | None = typer.Option(None, "--model"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Inspect provider defaults and exact model-level capability overrides."""
    value = _call(lambda: _service.capabilities(provider=provider, model=model))
    _render(value, as_json=as_json)


@app.command("fallback")
def fallback(as_json: bool = typer.Option(False, "--json")) -> None:
    """Show fallback policy and configured candidate order without executing it."""
    _render(_call(_service.fallback_summary), as_json=as_json)


@app.command("credentials")
def credentials(as_json: bool = typer.Option(False, "--json")) -> None:
    """Show safe local credential source and masking metadata."""
    value = _call(_service.credentials_summary)
    _render(value, as_json=as_json)


@app.command("health")
def health(as_json: bool = typer.Option(False, "--json")) -> None:
    """Show passively collected provider health snapshots."""
    _render(_call(_service.health_summary), as_json=as_json)


@app.command("observability")
def observability(
    as_json: bool = typer.Option(False, "--json"),
    text: bool = typer.Option(False, "--text"),
) -> None:
    """Show EventBus, subscriber, adapter, and recent-event metadata."""
    if as_json and text:
        _call(lambda: (_ for _ in ()).throw(ValueError("choose --json or --text")))
    _render(_call(_service.observability_summary), as_json=as_json)


@app.command("breaker")
def breaker(as_json: bool = typer.Option(False, "--json")) -> None:
    """Show passive provider circuit breaker state without changing it."""
    _render(_call(_service.breaker_summary), as_json=as_json)


@app.command("routing")
def routing(as_json: bool = typer.Option(False, "--json")) -> None:
    """Show registered routing metadata and a passive simulated decision."""
    _render(_call(_service.routing_summary), as_json=as_json)


@app.command("load")
def load(as_json: bool = typer.Option(False, "--json")) -> None:
    """Show stable process-local provider load snapshots without probing APIs."""
    _render(_call(_service.load_summary), as_json=as_json)


@app.command("rate-limit")
def rate_limit(as_json: bool = typer.Option(False, "--json")) -> None:
    """Show stable local provider quota snapshots without probing APIs."""
    _render(_call(_service.rate_limit_summary), as_json=as_json)


@app.command("cache")
def cache(as_json: bool = typer.Option(False, "--json")) -> None:
    """Show safe local cache backend statistics without cached values."""
    _render(_call(_service.cache_summary), as_json=as_json)


@app.command("plugins")
def plugins(as_json: bool = typer.Option(False, "--json")) -> None:
    """Show loaded local plugin metadata without loading or running plugins."""
    _render(_call(_service.plugins_summary), as_json=as_json)


@app.command("policy")
def policy(as_json: bool = typer.Option(False, "--json")) -> None:
    """Show optional policy registry metadata without evaluating policies."""
    _render(_call(_service.policy_summary), as_json=as_json)


@app.command("retry")
def retry(as_json: bool = typer.Option(False, "--json")) -> None:
    """Show explicit retry policy metadata without running a retry operation."""
    _render(_call(_service.retry_summary), as_json=as_json)


@app.command("distributed")
def distributed(as_json: bool = typer.Option(False, "--json")) -> None:
    """Show explicit local distributed runtime metadata without starting it."""
    _render(_call(_service.distributed_summary), as_json=as_json)


@app.command("telemetry")
def telemetry(as_json: bool = typer.Option(False, "--json")) -> None:
    """Show local telemetry metadata without enabling export."""
    _render(_call(_service.telemetry_summary), as_json=as_json)


@app.command("adaptive-routing")
def adaptive_routing(as_json: bool = typer.Option(False, "--json")) -> None:
    """Show optional local adaptive-routing history and score configuration."""
    _render(_call(_service.adaptive_summary), as_json=as_json)


@app.command("config")
def config(
    as_json: bool = typer.Option(False, "--json"),
    text: bool = typer.Option(False, "--text"),
) -> None:
    """Show resolved local configuration source and override metadata."""
    if as_json and text:
        _call(lambda: (_ for _ in ()).throw(ValueError("choose --json or --text")))
    _render(_call(_service.configuration_summary), as_json=as_json)


@app.command("validate-config")
def validate_config(as_json: bool = typer.Option(False, "--json")) -> None:
    """Run registry, configuration, and capability diagnostics only."""
    report = _call(_service.validate_config)
    if as_json:
        _render(report.to_dict(), as_json=True)
    else:
        typer.echo(report.to_text())
    _exit_for_report(report)


@app.command("version")
def version(as_json: bool = typer.Option(False, "--json")) -> None:
    """Display TKAI, Python, and runtime implementation versions."""
    _render(_call(_service.version), as_json=as_json)


@app.command("info")
def info(
    name: str | None = typer.Argument(None),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Display framework summary or legacy metadata for one named provider."""
    value = _call(lambda: _service.provider(name) if name else _service.info())
    _render(value, as_json=as_json)


# Compatibility aliases preserve the previously public ``tkai ai`` commands.
@app.command("list")
def list_providers() -> None:
    """Compatibility alias for :command:`tkai ai providers`."""
    for item in _call(_service.providers):
        typer.echo(item["provider"])


@app.command("models")
def models(name: str | None = None) -> None:
    """Compatibility command that delegates model lookup to the service facade."""
    for model in _call(lambda: _service.models(name)):
        typer.echo(model)


@app.command("chat")
def chat(
    message: str = typer.Option(..., "--message"),  # noqa: B008
    provider: str | None = typer.Option(None, "--provider"),
    model: str | None = typer.Option(None, "--model"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Compatibility chat command routed through :class:`ProviderManager`."""
    response = _call(lambda: _service.chat(message, provider=provider, model=model))
    _render(response.to_dict() if as_json else response.content, as_json=as_json)


@app.command("embed")
def embed(
    text: str = typer.Option(..., "--text"),  # noqa: B008
    provider: str | None = typer.Option(None, "--provider"),
    model: str | None = typer.Option(None, "--model"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Compatibility embedding command routed through :class:`ProviderManager`."""
    response = _call(lambda: _service.embed(text, provider=provider, model=model))
    _render(
        response.to_dict() if as_json else str(response.embeddings), as_json=as_json
    )
