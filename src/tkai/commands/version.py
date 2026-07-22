"""
TKAI Version Command
"""

from __future__ import annotations

import typer

from tkai import __version__

app = typer.Typer(
    help="Show TKAI version information.",
)


@app.command(name="show")
def show() -> None:
    """
    Show TKAI version.
    """
    typer.echo(f"TKAI v{__version__}")


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
) -> None:
    """
    Default version command.
    """
    if ctx.invoked_subcommand is None:
        show()