"""Studio visual-model tests remain independent from the runtime implementation."""

from __future__ import annotations

import pytest

from studio.shared import StudioNode, StudioNodeKind, StudioProject, StudioWorkflow


def test_visual_workflow_models_are_immutable_and_defensively_copy_metadata() -> None:
    """Designer declarations retain isolated configuration and metadata snapshots."""
    metadata = {"owner": "local"}
    config = {"tool": "echo"}
    project = StudioProject("project-1", "Local", metadata=metadata)
    node = StudioNode("node-1", StudioNodeKind.TOOL, "Echo", configuration=config)
    workflow = StudioWorkflow("workflow-1", project.project_id, "Flow", (node,))

    metadata["owner"] = "changed"
    config["tool"] = "changed"

    assert project.metadata["owner"] == "local"
    assert workflow.nodes[0].configuration["tool"] == "echo"
    with pytest.raises(TypeError):
        project.metadata["other"] = "value"  # type: ignore[index]


def test_visual_workflow_rejects_unknown_edges_and_duplicate_nodes() -> None:
    """The designer graph performs structural validation without workflow execution."""
    first = StudioNode("first", StudioNodeKind.AGENT, "Agent")
    with pytest.raises(ValueError, match="unique"):
        StudioWorkflow("workflow", "project", "Workflow", (first, first))
    with pytest.raises(ValueError, match="edges"):
        StudioWorkflow(
            "workflow", "project", "Workflow", (first,), (("first", "next"),)
        )
