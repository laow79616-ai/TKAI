"""Safe provider discovery commands; credentials are supplied by application code."""

from __future__ import annotations

import json

import typer

from tkai.ai import ChatMessage, ChatRequest, EmbeddingRequest, ProviderManager

app = typer.Typer(help="Inspect and invoke configured AI providers.")
_manager = ProviderManager()


@app.command("list")
def list_providers() -> None:
    """List registered provider instances."""
    for name in _manager.names():
        typer.echo(name)


@app.command("info")
def info(name: str) -> None:
    """Show non-secret provider metadata."""
    provider = _manager.get(name)
    typer.echo(f"{provider.name}: {provider.default_model}")


@app.command("models")
def models(name: str | None = None) -> None:
    """List models for the selected provider."""
    provider = _manager.get(name)
    for model in provider.list_models():
        typer.echo(model.id)


@app.command("doctor")
def doctor() -> None:
    """Check configured providers without exposing secrets."""
    unhealthy = [
        name for name in _manager.names() if not _manager.get(name).health_check()
    ]
    if unhealthy:
        typer.echo(f"unhealthy: {', '.join(unhealthy)}")
        raise typer.Exit(1)
    typer.echo("ok: no configured providers" if not _manager.names() else "ok")


@app.command("chat")
def chat(
    message: str = typer.Option(..., "--message"),  # noqa: B008
    provider: str | None = typer.Option(None, "--provider"),
    model: str | None = typer.Option(None, "--model"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Send a chat message through a configured provider."""
    response = _manager.chat(
        ChatRequest((ChatMessage("user", message),), model), provider=provider
    )
    typer.echo(json.dumps(response.to_dict()) if as_json else response.content)


@app.command("embed")
def embed(
    text: str = typer.Option(..., "--text"),  # noqa: B008
    provider: str | None = typer.Option(None, "--provider"),
    model: str | None = typer.Option(None, "--model"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Create embeddings through a configured provider."""
    response = _manager.embed(EmbeddingRequest((text,), model), provider=provider)
    typer.echo(json.dumps(response.to_dict()) if as_json else str(response.embeddings))
