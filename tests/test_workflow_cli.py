"""End-to-end coverage for the workflow release CLI."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from tkai.cli import app
from tkai.workflow import WorkflowEngine, WorkflowStatus
from tkai.workflow.examples import definitions

runner = CliRunner()


def test_workflow_list_info_validate_and_doctor() -> None:
    listed = runner.invoke(app, ["workflow", "list"])
    info = runner.invoke(app, ["workflow", "info", "hello-workflow"])
    validated = runner.invoke(app, ["workflow", "validate", "serial-example"])
    doctor = runner.invoke(app, ["workflow", "doctor"])

    assert listed.exit_code == 0
    assert "checkpoint-example" in listed.stdout
    assert info.exit_code == 0
    assert "hello-workflow" in info.stdout
    assert validated.exit_code == 0
    assert validated.stdout.strip() == "valid"
    assert doctor.exit_code == 0
    assert "ok:" in doctor.stdout


def test_workflow_run_supports_json_input_and_json_output() -> None:
    result = runner.invoke(
        app,
        [
            "workflow",
            "run",
            "hello-workflow",
            "--input",
            '{"name": "TKAI"}',
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "COMPLETED"
    assert payload["output"] == ["hello TKAI"]


def test_workflow_run_supports_yaml_input_file(tmp_path) -> None:
    input_file = tmp_path / "input.yaml"
    input_file.write_text("name: YAML\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["workflow", "run", "hello-workflow", "--input-file", str(input_file)],
    )

    assert result.exit_code == 0
    assert "hello YAML" in result.stdout


def test_workflow_run_supports_json_input_file(tmp_path) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text('{"name": "JSON file"}', encoding="utf-8")

    result = runner.invoke(
        app,
        ["workflow", "run", "hello-workflow", "--input-file", str(input_file)],
    )

    assert result.exit_code == 0
    assert "hello JSON file" in result.stdout


def test_workflow_checkpoint_and_resume_round_trip(tmp_path) -> None:
    checkpoint_file = tmp_path / "workflow.json"
    checkpoint = runner.invoke(
        app,
        [
            "workflow",
            "checkpoint",
            "serial-example",
            "--output",
            str(checkpoint_file),
        ],
    )
    resumed = runner.invoke(
        app,
        [
            "workflow",
            "resume",
            "serial-example",
            "--checkpoint",
            str(checkpoint_file),
            "--json",
        ],
    )

    assert checkpoint.exit_code == 0
    assert json.loads(checkpoint_file.read_text(encoding="utf-8"))["state"] == "PAUSED"
    assert resumed.exit_code == 0
    assert json.loads(resumed.stdout)["status"] == "COMPLETED"


def test_workflow_cli_uses_nonzero_exit_codes_for_invalid_requests() -> None:
    unknown = runner.invoke(app, ["workflow", "run", "missing-workflow"])
    malformed = runner.invoke(
        app,
        ["workflow", "run", "hello-workflow", "--input", "not-json"],
    )

    assert unknown.exit_code != 0
    assert malformed.exit_code != 0


def test_all_builtin_workflow_examples_execute_without_external_services() -> None:
    engine = WorkflowEngine()

    results = [engine.execute(definition) for definition in definitions()]

    assert len(results) == 7
    assert all(result.status is WorkflowStatus.COMPLETED for result in results)
