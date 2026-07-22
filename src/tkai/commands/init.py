"""
TKAI Init Command
"""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(
    help="Initialize TKAI configuration.",
)


def _initialize() -> None:
    """
    Initialize TKAI workspace.
    """

    workspace = Path.cwd()

    config_dir = workspace / ".tkai"

    config_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    typer.secho(
        f"Initialized TKAI workspace: {workspace}",
        fg=typer.colors.GREEN,
    )


@app.command(name="run")
def run() -> None:
    """
    Initialize current workspace.
    """

    _initialize()


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
) -> None:
    """
    Default init command.
    """

    if ctx.invoked_subcommand is None:
        run()