"""Visual workflow designer state and validation."""

from dataclasses import replace

from workflow_platform.models import Edge, Node, NodeType, Workflow


class Designer:
    def __init__(self, workflow: Workflow) -> None:
        self._versions = [workflow]
        self._cursor = 0

    @property
    def workflow(self) -> Workflow:
        return self._versions[self._cursor]

    def update(self, *, nodes: tuple[Node, ...], edges: tuple[Edge, ...]) -> Workflow:
        updated = replace(
            self.workflow,
            nodes=nodes,
            edges=edges,
            version=self.workflow.version + 1,
        )
        self._versions = self._versions[: self._cursor + 1] + [updated]
        self._cursor += 1
        return updated

    def undo(self) -> Workflow:
        self._cursor = max(0, self._cursor - 1)
        return self.workflow

    def redo(self) -> Workflow:
        self._cursor = min(len(self._versions) - 1, self._cursor + 1)
        return self.workflow

    def validate(self) -> tuple[str, ...]:
        nodes = {node.id: node for node in self.workflow.nodes}
        errors: list[str] = []
        if sum(node.type is NodeType.START for node in nodes.values()) != 1:
            errors.append("Workflow requires exactly one start node.")
        if not any(node.type is NodeType.END for node in nodes.values()):
            errors.append("Workflow requires an end node.")
        for edge in self.workflow.edges:
            if edge.source not in nodes or edge.target not in nodes:
                errors.append("Every edge must reference existing nodes.")
        return tuple(dict.fromkeys(errors))
