from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExecutionEvent:
    execution_id: str
    name: str


@dataclass(frozen=True, slots=True)
class ExecutionHistory:
    events: tuple[ExecutionEvent, ...] = ()


@dataclass(frozen=True, slots=True)
class ExecutionSummary:
    execution_id: str
    event_count: int = 0
