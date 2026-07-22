"""Workflow command group."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
import yaml

from tkai.workflow import WorkflowEngine, WorkflowRegistry
from tkai.workflow.examples import definitions

app = typer.Typer(help="Manage TKAI workflows.")
_registry = WorkflowRegistry()
for _definition in definitions():
    _registry.register(_definition)


@app.command("list")
def list_workflows() -> None:
    for name in _registry.list():
        typer.echo(name)


@app.command("doctor")
def doctor() -> None:
    typer.echo("workflow registry available")


@app.command("info")
def info(name: str) -> None:
    definition = _registry.get(name)
    typer.echo(f"{definition.name}: {definition.description}")


@app.command("validate")
def validate(name: str) -> None:
    _registry.get(name)
    typer.echo("valid")


@app.command("run")
def run(
    name: str,
    input: str | None = typer.Option(None, "--input"),
    input_file: Path | None = typer.Option(None, "--input-file"),  # noqa: B008
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    values: dict[str, Any] = json.loads(input) if input else {}
    if input_file:
        loaded = yaml.safe_load(input_file.read_text(encoding="utf-8")) or {}
        if not isinstance(loaded, dict):
            raise typer.BadParameter("input file must contain an object")
        values.update(loaded)
    result = WorkflowEngine().execute(_registry.get(name), values)
    if as_json:
        typer.echo(json.dumps(result.to_dict(), default=str))
    else:
        typer.echo(f"{result.status.name.lower()}: {result.output}")
    if result.status.name == "FAILED":
        raise typer.Exit(1)
