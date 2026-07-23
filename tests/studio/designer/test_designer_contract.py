"""Offline static contract checks for the frontend Workflow Designer reference."""

from __future__ import annotations

from pathlib import Path


def test_designer_models_validation_json_rest_mapping_and_components_exist() -> None:
    root = Path(__file__).resolve().parents[3] / "studio" / "frontend" / "src"
    workflow = (root / "workflow.ts").read_text(encoding="utf-8")
    components = (root / "designer-components.tsx").read_text(encoding="utf-8")
    for token in (
        "grid", "zoom", "pan", "selection", "connect", "disconnect",
        "validate", "snapshot", "restore", "exportJson", "importJson",
        "toWorkflowPayload", "referenceWorkflow",
    ):
        assert token in workflow
    for node in ("task", "condition", "loop", "retry", "parallel", "branch", "end"):
        assert f'"{node}"' in workflow
    for component in (
        "WorkflowCanvas", "WorkflowNode", "WorkflowEdge", "WorkflowToolbar",
        "PropertyPanel", "ValidationPanel", "MiniMap",
    ):
        assert component in components
