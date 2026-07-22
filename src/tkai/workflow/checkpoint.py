"""JSON-safe, in-memory snapshots of workflow runtime state."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Any, cast

from .runtime import WorkflowRuntime


def _json_safe(value: Any) -> Any:
    """Convert a value to a JSON-compatible representation.

    Handler outputs are intentionally allowed to be arbitrary Python values.  A
    checkpoint must nevertheless always be exportable, so unknown values are
    represented by their ``repr`` rather than making recovery unavailable.
    """
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [_json_safe(item) for item in value]
    return repr(value)


@dataclass(slots=True)
class Checkpoint:
    """A complete, portable record of a runtime's scheduling state."""

    context: dict[str, Any]
    state: str
    ready: list[str] = field(default_factory=list)
    waiting: list[str] = field(default_factory=list)
    running: list[str] = field(default_factory=list)
    completed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    cancelled: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    retries: dict[str, int] = field(default_factory=dict)
    step_results: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a detached JSON-compatible checkpoint payload."""
        return cast(dict[str, Any], _json_safe(asdict(self)))

    def to_json(self) -> str:
        """Export this checkpoint as stable JSON."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Checkpoint:
        """Construct a checkpoint from an already decoded payload."""
        fields = {
            "context",
            "state",
            "ready",
            "waiting",
            "running",
            "completed",
            "failed",
            "cancelled",
            "skipped",
            "retries",
            "step_results",
        }
        payload = {name: data[name] for name in fields if name in data}
        return cls(**payload)

    @classmethod
    def from_json(cls, data: str) -> Checkpoint:
        """Import a checkpoint exported by :meth:`to_json`."""
        decoded = json.loads(data)
        if not isinstance(decoded, dict):
            raise ValueError("Checkpoint JSON must describe an object")
        return cls.from_dict(decoded)


class CheckpointManager:
    """Create, retain, import, and export checkpoints in process memory."""

    def __init__(self) -> None:
        self._items: dict[str, Checkpoint] = {}

    def create_checkpoint(self, name: str, runtime: WorkflowRuntime) -> Checkpoint:
        """Capture the runtime without retaining mutable references to it."""
        ready = [runtime.step_name(step) for step in runtime.dispatcher.next_ready()]
        checkpoint = Checkpoint(
            context={
                "inputs": runtime.context.workflow.inputs,
                "shared": runtime.context.workflow.shared,
                "results": runtime.context.workflow.results,
                "previous_result": runtime.context.workflow.previous_result,
            },
            state=runtime.context.state.name,
            ready=ready,
            waiting=[
                runtime.step_name(step)
                for step in runtime.dispatcher.pending
                if runtime.step_name(step) not in ready
            ],
            running=sorted(runtime.context.running),
            completed=sorted(runtime.context.completed),
            failed=sorted(runtime.context.failed),
            cancelled=sorted(runtime.context.cancelled),
            skipped=sorted(runtime.context.skipped),
            retries=dict(runtime.context.retries),
            step_results=deepcopy(runtime.context.step_results),
        )
        self._items[name] = Checkpoint.from_dict(checkpoint.to_dict())
        return Checkpoint.from_dict(checkpoint.to_dict())

    def load_checkpoint(self, name: str) -> Checkpoint:
        """Load a detached copy of a named in-memory checkpoint."""
        try:
            checkpoint = self._items[name]
        except KeyError as exc:
            raise KeyError(f"Checkpoint '{name}' was not found") from exc
        return Checkpoint.from_dict(checkpoint.to_dict())

    def export_checkpoint(self, name: str) -> str:
        """Export a named checkpoint as JSON."""
        return self.load_checkpoint(name).to_json()

    def import_checkpoint(self, name: str, data: str) -> Checkpoint:
        """Import JSON and store it under ``name`` in this process."""
        checkpoint = Checkpoint.from_json(data)
        self._items[name] = Checkpoint.from_dict(checkpoint.to_dict())
        return self.load_checkpoint(name)
