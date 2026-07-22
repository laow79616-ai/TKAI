"""
TKAI Template Command
"""

from __future__ import annotations

from pathlib import Path

import typer

from tkai.template_engine import TemplateManager

app = typer.Typer(
    help="Template management.",
)


def get_manager() -> TemplateManager:
    """
    Return template manager.
    """

    template_root = (
        Path(__file__).resolve().parent.parent
        / "templates"
    )

    return TemplateManager(template_root)


@app.command("list")
def list_templates() -> None:
    """
    List all templates.
    """

    manager = get_manager()

    typer.echo("")
    typer.echo("=" * 60)
    typer.echo("Available Templates")
    typer.echo("=" * 60)

    for name in manager.list():
        typer.echo(f"• {name}")


@app.command("info")
def info(
    template: str = typer.Argument(
        ...,
        help="Template name.",
    ),
) -> None:
    """
    Show template information.
    """

    manager = get_manager()

    manifest = manager.manifest(template)

    typer.echo("")
    typer.echo("=" * 60)
    typer.echo("Template Information")
    typer.echo("=" * 60)

    typer.echo(f"Name        : {manifest.name}")
    typer.echo(f"Version     : {manifest.version}")
    typer.echo(f"Author      : {manifest.author}")
    typer.echo(f"Description : {manifest.description}")
    typer.echo(f"License     : {manifest.license}")
    typer.echo(f"Homepage    : {manifest.homepage}")


@app.command("validate")
def validate() -> None:
    """
    Validate templates.
    """

    manager = get_manager()

    failed = False

    for template in manager.list():
        try:
            manager.manifest(template)
            typer.secho(
                f"✓ {template}",
                fg=typer.colors.GREEN,
            )
        except Exception as exc:
            failed = True
            typer.secho(
                f"✗ {template}: {exc}",
                fg=typer.colors.RED,
            )

    if failed:
        raise typer.Exit(code=1)


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
) -> None:
    """
    Default template command.
    """

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())