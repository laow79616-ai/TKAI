"""
TKAI Doctor Command
"""

from __future__ import annotations

import platform
import sys
from pathlib import Path

import typer

app = typer.Typer(
    help="Check the TKAI development environment.",
)


def _check_python() -> str:
    return platform.python_version()


def _check_platform() -> str:
    return platform.platform()


def _check_workspace() -> str:
    return str(Path.cwd())


@app.command(name="run")
def run() -> None:
    """
    Run environment diagnostics.
    """

    typer.echo("")
    typer.echo("=" * 60)
    typer.echo("TKAI Environment Check")
    typer.echo("=" * 60)
    typer.echo("")

    typer.echo(f"Python     : {_check_python()}")
    typer.echo(f"Platform   : {_check_platform()}")
    typer.echo(f"Executable : {sys.executable}")
    typer.echo(f"Workspace  : {_check_workspace()}")

    typer.echo("")
    typer.secho(
        "Environment check completed.",
        fg=typer.colors.GREEN,
    )


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
) -> None:
    """
    Default doctor command.
    """

    if ctx.invoked_subcommand is None:
        run()