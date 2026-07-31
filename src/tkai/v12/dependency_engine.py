"""Read-only dependency and relationship analysis."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DependencyFinding:
    kind: str
    subject: str
    reference: str
    severity: str = "review-required"


class DependencyAnalyzer:
    def analyze(
        self,
        graph: dict[str, tuple[str, ...]],
        *,
        maximum_nodes: int = 1000,
        maximum_dependencies: int = 128,
    ) -> tuple[DependencyFinding, ...]:
        if len(graph) > maximum_nodes:
            raise ValueError("node count exceeds bound")
        known = frozenset(graph)
        findings: list[DependencyFinding] = []
        for node, references in sorted(graph.items()):
            if len(references) > maximum_dependencies:
                raise ValueError("dependency count exceeds bound")
            for reference in references:
                if reference not in known:
                    findings.append(
                        DependencyFinding("missing-dependency", node, reference)
                    )
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str, path: tuple[str, ...]) -> None:
            if node in visiting:
                findings.append(
                    DependencyFinding(
                        "circular-dependency", node, " -> ".join((*path, node))
                    )
                )
                return
            if node in visited or node not in graph:
                return
            visiting.add(node)
            for dependency in graph[node]:
                visit(dependency, (*path, node))
            visiting.remove(node)
            visited.add(node)

        for node in sorted(graph):
            visit(node, ())
        unique = {(item.kind, item.subject, item.reference): item for item in findings}
        return tuple(unique[key] for key in sorted(unique))
