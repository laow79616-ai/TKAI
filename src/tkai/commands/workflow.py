"""Workflow lifecycle, validation, checkpoint, and recovery commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
import yaml

from tkai.workflow import (
    Checkpoint,
    Workflow,
    WorkflowDefinition,
    WorkflowEngine,
    WorkflowRegistry,
    WorkflowStatus,
)
from tkai.workflow.examples import definitions

app = typer.Typer(help="Manage TKAI workflows.")
_registry = WorkflowRegistry()
for _definition in definitions():
    _registry.register(_definition)


def _get_definition(name: str) -> WorkflowDefinition:
    """Return a registered definition or present a concise CLI error."""
    try:
        return _registry.get(name)
    except Exception as exc:
        raise typer.BadParameter(f"Unknown workflow: {name}") from exc


def _validate_definition(definition: WorkflowDefinition) -> list[str]:
    """Return deterministic structural validation errors for a definition."""
    names = [step.name or step.task.name for step in definition.steps]
    errors: list[str] = []
    if len(names) != len(set(names)):
        errors.append("workflow contains duplicate step names")
    known = set(names)
    for step in definition.steps:
        missing = set(step.dependency_names) - known
        if missing:
            missing_names = ", ".join(sorted(missing))
            errors.append(
                f"step '{step.name}' has missing dependencies: {missing_names}"
            )
    graph = {
        step.name or step.task.name: set(step.dependency_names)
        for step in definition.steps
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> bool:
        if name in visiting:
            return True
        if name in visited:
            return False
        visiting.add(name)
        cyclic = any(
            dependency in graph and visit(dependency) for dependency in graph[name]
        )
        visiting.remove(name)
        visited.add(name)
        return cyclic

    if any(visit(name) for name in graph):
        errors.append("workflow contains a circular step dependency")
    return errors


def _load_inputs(input_value: str | None, input_file: Path | None) -> dict[str, Any]:
    """Read JSON command input plus JSON or YAML object files."""
    values: dict[str, Any] = {}
    if input_value:
        try:
            loaded = json.loads(input_value)
        except json.JSONDecodeError as exc:
            raise typer.BadParameter("--input must contain a JSON object") from exc
        if not isinstance(loaded, dict):
            raise typer.BadParameter("--input must contain a JSON object")
        values.update(loaded)
    if input_file:
        try:
            loaded = yaml.safe_load(input_file.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError) as exc:
            raise typer.BadParameter(
                f"Unable to load input file: {input_file}"
            ) from exc
        if not isinstance(loaded, dict):
            raise typer.BadParameter("input file must contain an object")
        values.update(loaded)
    return values


def _paused_workflow(definition: WorkflowDefinition) -> Workflow:
    """Build the public workflow model required by the resume facade."""
    workflow = Workflow(definition)
    workflow.transition(WorkflowStatus.VALIDATED)
    workflow.transition(WorkflowStatus.PENDING)
    workflow.transition(WorkflowStatus.RUNNING)
    workflow.pause()
    return workflow


def _print_result(result: Any, as_json: bool) -> None:
    """Render workflow results in human-friendly or machine-readable form."""
    if as_json:
        typer.echo(json.dumps(result.to_dict(), default=str, sort_keys=True))
    else:
        typer.echo(f"{result.status.name.lower()}: {result.output}")


@app.command("list")
def list_workflows() -> None:
    """List registered workflows in stable name order."""
    for name in _registry.list():
        typer.echo(name)


@app.command("doctor")
def doctor() -> None:
    """Validate every registered workflow and return a useful exit status."""
    errors = {
        definition.name: _validate_definition(definition)
        for definition in (_registry.get(name) for name in _registry.list())
    }
    invalid = {name: messages for name, messages in errors.items() if messages}
    if invalid:
        for name, messages in invalid.items():
            typer.echo(f"{name}: {'; '.join(messages)}")
        raise typer.Exit(1)
    typer.echo(f"ok: {len(errors)} workflow(s) validated")


@app.command("info")
def info(name: str) -> None:
    """Describe one registered workflow."""
    definition = _get_definition(name)
    typer.echo(f"{definition.name}: {definition.description}")
    steps = ", ".join(step.name or step.task.name for step in definition.steps)
    typer.echo(f"steps: {steps}")


@app.command("validate")
def validate(name: str) -> None:
    """Validate dependency names and cycles for one workflow."""
    errors = _validate_definition(_get_definition(name))
    if errors:
        typer.echo("; ".join(errors))
        raise typer.Exit(1)
    typer.echo("valid")


@app.command("run")
def run(
    name: str,
    input: str | None = typer.Option(None, "--input"),
    input_file: Path | None = typer.Option(None, "--input-file"),  # noqa: B008
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Run a workflow with JSON text or JSON/YAML file input."""
    definition = _get_definition(name)
    errors = _validate_definition(definition)
    if errors:
        typer.echo("; ".join(errors))
        raise typer.Exit(1)
    result = WorkflowEngine().execute(definition, _load_inputs(input, input_file))
    _print_result(result, as_json)
    if result.status is not WorkflowStatus.COMPLETED:
        raise typer.Exit(1)


@app.command("checkpoint")
def checkpoint(
    name: str,
    output: Path = typer.Option(..., "--output"),  # noqa: B008
    input: str | None = typer.Option(None, "--input"),
    input_file: Path | None = typer.Option(None, "--input-file"),  # noqa: B008
) -> None:
    """Write a paused, recoverable initial checkpoint for a workflow."""
    definition = _get_definition(name)
    errors = _validate_definition(definition)
    if errors:
        typer.echo("; ".join(errors))
        raise typer.Exit(1)
    engine = WorkflowEngine()
    runtime = engine.create_runtime(definition, _load_inputs(input, input_file))
    snapshot = engine.pause(runtime, definition.name)
    output.write_text(snapshot.to_json(), encoding="utf-8")
    typer.echo(str(output))


@app.command("resume")
def resume(
    name: str,
    checkpoint_file: Path = typer.Option(..., "--checkpoint"),  # noqa: B008
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Resume a named workflow from a JSON checkpoint file."""
    definition = _get_definition(name)
    try:
        snapshot = Checkpoint.from_json(checkpoint_file.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            "--checkpoint must contain valid checkpoint JSON"
        ) from exc
    result = WorkflowEngine().resume(_paused_workflow(definition), snapshot.to_dict())
    _print_result(result, as_json)
    if result.status is not WorkflowStatus.COMPLETED:
        raise typer.Exit(1)
