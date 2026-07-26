"""Bounded connector contracts; no connector performs network I/O."""

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ConnectorRequest:
    operation: str
    payload: dict[str, Any]
    limit: int = 100

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 1000:
            raise ValueError("Connector limit must be between 1 and 1000.")


class Connector(Protocol):
    kind: str

    def execute(self, request: ConnectorRequest) -> dict[str, Any]: ...


class BoundedConnector:
    def __init__(self, kind: str, fixtures: dict[str, Any] | None = None) -> None:
        if kind not in {"rest", "webhook", "email", "database", "queue", "storage"}:
            raise ValueError("Unsupported connector kind.")
        self.kind = kind
        self.fixtures = fixtures or {}

    def execute(self, request: ConnectorRequest) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "operation": request.operation,
            "data": self.fixtures.get(request.operation),
            "bounded": True,
        }
