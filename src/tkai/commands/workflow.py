"""Workflow command group."""

from __future__ import annotations

import typer

from tkai.workflow import WorkflowRegistry

app = typer.Typer(help="Manage TKAI workflows.")
_registry = WorkflowRegistry()


@app.command("list")
def list_workflows() -> None:
    for name in _registry.list():
        typer.echo(name)


@app.command("doctor")
def doctor() -> None:
    typer.echo("workflow registry available")
