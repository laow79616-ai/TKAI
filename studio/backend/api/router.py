"""Dependency-free REST controller methods consumed by the optional FastAPI host."""

from __future__ import annotations

from collections.abc import Mapping

from studio.backend.dependencies import StudioDependencies
from studio.backend.errors import StudioValidationError
from studio.shared import StudioNode, StudioNodeKind, StudioWorkflow


class StudioAPI:
    """Translate simple JSON-compatible payloads to explicit Studio services."""

    def __init__(self, dependencies: StudioDependencies) -> None:
        self._dependencies = dependencies

    def health(self) -> dict[str, object]:
        """Return the passive local health report."""
        return self._dependencies.health_service.report()

    def system(self) -> dict[str, object]:
        """Return safe Studio and TKAI system metadata."""
        return self._dependencies.system_service.report()

    def version(self) -> dict[str, object]:
        """Return the frozen Studio and TKAI version subset."""
        system = self.system()
        return {"studio": system["studio"], "tkai_version": system["tkai_version"]}

    def create_project(self, payload: Mapping[str, object]) -> dict[str, object]:
        """Create a project from a small JSON-compatible payload."""
        name = _required_string(payload, "name")
        description = _optional_string(payload, "description", "")
        project_id = _optional_string(payload, "project_id", None)
        metadata = _mapping(payload.get("metadata", {}), "metadata")
        project = self._dependencies.project_service.create(
            name,
            description="" if description is None else description,
            metadata=metadata,
            project_id=project_id,
        )
        return _project_payload(project)

    def list_projects(self) -> list[dict[str, object]]:
        """List project payloads in deterministic repository order."""
        return [
            _project_payload(item) for item in self._dependencies.project_service.list()
        ]

    def get_project(self, project_id: str) -> dict[str, object]:
        """Return one project payload."""
        return _project_payload(self._dependencies.project_service.get(project_id))

    def update_project(
        self, project_id: str, payload: Mapping[str, object]
    ) -> dict[str, object]:
        """Patch a project with explicit optional fields."""
        project = self._dependencies.project_service.update(
            project_id,
            name=_optional_string(payload, "name", None),
            description=_optional_string(payload, "description", None),
            metadata=_mapping_or_none(payload.get("metadata"), "metadata"),
        )
        return _project_payload(project)

    def delete_project(self, project_id: str) -> dict[str, object]:
        """Delete a project and return a stable acknowledgement."""
        self._dependencies.project_service.delete(project_id)
        return {"deleted": project_id}

    def create_workflow(self, payload: Mapping[str, object]) -> dict[str, object]:
        """Create a visual workflow declaration without compiling it to SDK nodes."""
        workflow = _workflow_from_payload(payload)
        return _workflow_payload(self._dependencies.workflow_service.create(workflow))

    def list_workflows(self, project_id: str | None = None) -> list[dict[str, object]]:
        """List visual workflows, optionally filtered by project."""
        return [
            _workflow_payload(item)
            for item in self._dependencies.workflow_service.list(project_id=project_id)
        ]

    def get_workflow(self, workflow_id: str) -> dict[str, object]:
        """Return one visual workflow payload."""
        return _workflow_payload(self._dependencies.workflow_service.get(workflow_id))

    def update_workflow(
        self, workflow_id: str, payload: Mapping[str, object]
    ) -> dict[str, object]:
        """Replace a visual workflow declaration whose id matches its route id."""
        return _workflow_payload(
            self._dependencies.workflow_service.update(
                workflow_id, _workflow_from_payload(payload)
            )
        )

    def delete_workflow(self, workflow_id: str) -> dict[str, object]:
        """Delete a visual workflow declaration."""
        self._dependencies.workflow_service.delete(workflow_id)
        return {"deleted": workflow_id}

    def create_execution(self, payload: Mapping[str, object]) -> dict[str, object]:
        """Execute an explicitly configured SDK workflow for a saved visual workflow."""
        execution = self._dependencies.execution_service.execute(
            _required_string(payload, "workflow_id")
        )
        return _execution_payload(execution)

    def list_executions(
        self,
        project_id: str | None = None,
        workflow_id: str | None = None,
    ) -> list[dict[str, object]]:
        """List execution records with deterministic local filters."""
        return [
            _execution_payload(item)
            for item in self._dependencies.execution_service.list(
                project_id=project_id, workflow_id=workflow_id
            )
        ]

    def get_execution(self, execution_id: str) -> dict[str, object]:
        """Return a single local execution record."""
        return _execution_payload(
            self._dependencies.execution_service.get(execution_id)
        )


def _required_string(payload: Mapping[str, object], name: str) -> str:
    """Extract a non-empty string from an API payload."""
    value = payload.get(name)
    if not isinstance(value, str) or not value:
        raise StudioValidationError(f"{name} must be a non-empty string.")
    return value


def _optional_string(
    payload: Mapping[str, object], name: str, default: str | None
) -> str | None:
    """Extract an optional string while preserving explicit empty-string validation."""
    value = payload.get(name, default)
    if value is None:
        return None
    if not isinstance(value, str):
        raise StudioValidationError(f"{name} must be a string.")
    return value


def _mapping(value: object, name: str) -> Mapping[str, object]:
    """Validate a mapping-like JSON field."""
    if not isinstance(value, Mapping):
        raise StudioValidationError(f"{name} must be an object.")
    return dict(value)


def _mapping_or_none(value: object, name: str) -> Mapping[str, object] | None:
    """Validate an optional mapping-like JSON field."""
    return None if value is None else _mapping(value, name)


def _workflow_from_payload(payload: Mapping[str, object]) -> StudioWorkflow:
    """Build an immutable visual workflow from a JSON-compatible payload."""
    node_values = payload.get("nodes", ())
    if not isinstance(node_values, (list, tuple)):
        raise StudioValidationError("nodes must be an array.")
    nodes = tuple(_node_from_payload(value) for value in node_values)
    edge_values = payload.get("edges", ())
    if not isinstance(edge_values, (list, tuple)):
        raise StudioValidationError("edges must be an array.")
    edges: list[tuple[str, str]] = []
    for edge in edge_values:
        if not isinstance(edge, (list, tuple)) or len(edge) != 2:
            raise StudioValidationError("Each edge must contain source and target ids.")
        source, target = edge
        if not isinstance(source, str) or not isinstance(target, str):
            raise StudioValidationError("Workflow edge ids must be strings.")
        edges.append((source, target))
    return StudioWorkflow(
        _required_string(payload, "workflow_id"),
        _required_string(payload, "project_id"),
        _required_string(payload, "name"),
        nodes,
        tuple(edges),
        _mapping(payload.get("metadata", {}), "metadata"),
    )


def _node_from_payload(value: object) -> StudioNode:
    """Build one immutable visual node from a JSON-compatible mapping."""
    payload = _mapping(value, "node")
    kind_value = _required_string(payload, "kind")
    try:
        kind = StudioNodeKind(kind_value)
    except ValueError as error:
        raise StudioValidationError(
            f"Unknown Studio node kind: {kind_value}"
        ) from error
    position = payload.get("position", (0, 0))
    if (
        not isinstance(position, (list, tuple))
        or len(position) != 2
        or not all(
            isinstance(item, int) and not isinstance(item, bool) for item in position
        )
    ):
        raise StudioValidationError("Node position must be a pair of integers.")
    return StudioNode(
        _required_string(payload, "node_id"),
        kind,
        _required_string(payload, "label"),
        (position[0], position[1]),
        _mapping(payload.get("configuration", {}), "configuration"),
    )


def _project_payload(project: object) -> dict[str, object]:
    """Serialize an immutable project model without exposing implementation state."""
    from studio.shared import StudioProject

    assert isinstance(project, StudioProject)
    return {
        "project_id": project.project_id,
        "name": project.name,
        "description": project.description,
        "metadata": dict(project.metadata),
        "created_at": project.created_at.isoformat(),
    }


def _workflow_payload(workflow: StudioWorkflow) -> dict[str, object]:
    """Serialize a visual workflow with deterministic node and edge content."""
    return {
        "workflow_id": workflow.workflow_id,
        "project_id": workflow.project_id,
        "name": workflow.name,
        "nodes": [
            {
                "node_id": node.node_id,
                "kind": node.kind.value,
                "label": node.label,
                "position": list(node.position),
                "configuration": dict(node.configuration),
            }
            for node in workflow.nodes
        ],
        "edges": [list(edge) for edge in workflow.edges],
        "metadata": dict(workflow.metadata),
    }


def _execution_payload(execution: object) -> dict[str, object]:
    """Serialize a local execution snapshot without internal exception objects."""
    from studio.shared import ExecutionRecord

    assert isinstance(execution, ExecutionRecord)
    return {
        "execution_id": execution.execution_id,
        "workflow_id": execution.workflow_id,
        "project_id": execution.project_id,
        "status": execution.status.value,
        "output": execution.output,
        "error": execution.error,
        "created_at": execution.created_at.isoformat(),
    }
