"""Deterministic, local-only reference execution for SDK workflow definitions."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Event, RLock
from time import monotonic
from types import MappingProxyType
from typing import cast

from .definitions import Node, NodeKind, WorkflowDefinition
from .hooks import WorkflowHook


class WorkflowState(str, Enum):
    """Reference workflow states exposed in results and snapshots."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


@dataclass(slots=True)
class ExecutionContext:
    """Explicit dependencies and mutable variables for one workflow execution."""

    variables: dict[str, object] = field(default_factory=dict)
    memory: object | None = None
    provider: object | None = None
    agent: object | None = None
    metadata: dict[str, object] = field(default_factory=dict)
    cancellation: Event = field(default_factory=Event)
    timeout_seconds: float | None = None
    context: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorkflowContext:
    """Node-scoped view over the explicitly supplied execution context."""

    execution: ExecutionContext
    node: Node

    @property
    def variables(self) -> dict[str, object]:
        """Return the current execution variables for the active node."""
        return self.execution.variables


@dataclass(frozen=True, slots=True)
class ExecutionEvent:
    """A timestamped local event with no external telemetry dependency."""

    name: str
    node: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    detail: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "detail", MappingProxyType(dict(self.detail)))


@dataclass(frozen=True, slots=True)
class WorkflowResult:
    """Immutable result of a complete or one-step reference execution."""

    state: WorkflowState
    output: object | None
    variables: Mapping[str, object]
    events: tuple[ExecutionEvent, ...]
    error: Exception | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "variables",
            MappingProxyType(deepcopy(dict(self.variables))),
        )


@dataclass(frozen=True, slots=True)
class WorkflowSnapshot:
    """In-memory resume point; it is not persistent workflow storage."""

    workflow_name: str
    state: WorkflowState
    current_node: str | None
    variables: Mapping[str, object]
    output: object | None
    events: tuple[ExecutionEvent, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "variables",
            MappingProxyType(deepcopy(dict(self.variables))),
        )


class WorkflowRuntime:
    """Explicit, synchronous, local reference runtime for a workflow definition."""

    def __init__(
        self,
        definition: WorkflowDefinition,
        *,
        hooks: tuple[WorkflowHook, ...] = (),
        max_steps: int = 1_000,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if max_steps < 1:
            raise ValueError("Workflow max_steps must be at least one.")
        self.definition = definition
        self._nodes = {node.name: node for node in definition.nodes}
        self._hooks = hooks
        self._max_steps = max_steps
        self._clock = clock
        self._lock = RLock()
        self._context: ExecutionContext | None = None
        self._current_node: str | None = None
        self._state = WorkflowState.PENDING
        self._events: list[ExecutionEvent] = []
        self._output: object | None = None
        self._error: Exception | None = None
        self._started_at: float | None = None
        self._steps = 0

    def execute(self, context: ExecutionContext | None = None) -> WorkflowResult:
        """Execute the local graph until it reaches a terminal reference state."""
        with self._lock:
            if context is not None or self._context is None or self._terminal:
                self._initialize(context or ExecutionContext())
            self._notify("before_execute")
            while not self._terminal:
                self.step()
            self._notify("after_execute")
            return self._result()

    def step(self) -> WorkflowResult:
        """Execute at most one graph node and expose a stable result snapshot."""
        with self._lock:
            if self._terminal:
                return self._result()
            if self._context is None:
                self._initialize(ExecutionContext())
            if self._terminal:
                return self._result()
            if self._cancelled_or_timed_out():
                return self._result()
            if self._steps >= self._max_steps:
                self._fail(RuntimeError("Workflow maximum step count exceeded."))
                return self._result()
            if self._current_node is None:
                self._state = WorkflowState.SUCCEEDED
                return self._result()

            node = self._nodes[self._current_node]
            self._steps += 1
            self._emit("node_started", node.name)
            self._notify("before_node", node)
            try:
                self._current_node = self._execute_node(node)
            except Exception as error:
                self._fail(error, node)
            else:
                self._notify("after_node", node)
                self._emit("node_completed", node.name)
                if self._current_node is None:
                    self._state = WorkflowState.SUCCEEDED
            return self._result()

    def resume(self) -> WorkflowResult:
        """Continue an active or restored workflow until its next terminal state."""
        return self.execute()

    def cancel(self) -> WorkflowResult:
        """Request cancellation; the next step observes it without background work."""
        with self._lock:
            if self._context is not None:
                self._context.cancellation.set()
            if not self._terminal:
                self._state = WorkflowState.CANCELLED
                self._emit("workflow_cancelled", self._current_node)
            return self._result()

    def snapshot(self) -> WorkflowSnapshot:
        """Return an isolated in-memory resume point for this reference execution."""
        with self._lock:
            variables = self._context.variables if self._context is not None else {}
            return WorkflowSnapshot(
                self.definition.name,
                self._state,
                self._current_node,
                variables,
                self._output,
                tuple(self._events),
            )

    def restore(
        self, snapshot: WorkflowSnapshot, context: ExecutionContext | None = None
    ) -> WorkflowResult:
        """Restore a compatible in-memory snapshot without persistence or I/O."""
        if snapshot.workflow_name != self.definition.name:
            raise ValueError("Workflow snapshot belongs to a different definition.")
        with self._lock:
            restored = context or ExecutionContext()
            restored.variables.update(deepcopy(dict(snapshot.variables)))
            self._context = restored
            self._current_node = snapshot.current_node
            self._state = snapshot.state
            self._events = list(snapshot.events)
            self._output = snapshot.output
            self._error = None
            self._started_at = self._clock()
            self._steps = 0
            return self._result()

    @property
    def _terminal(self) -> bool:
        return self._state in {
            WorkflowState.SUCCEEDED,
            WorkflowState.FAILED,
            WorkflowState.CANCELLED,
            WorkflowState.TIMED_OUT,
        }

    def _initialize(self, context: ExecutionContext) -> None:
        self._context = context
        self._current_node = self.definition.entrypoint
        self._state = WorkflowState.RUNNING
        self._events = []
        self._output = None
        self._error = None
        self._started_at = self._clock()
        self._steps = 0
        self._emit("workflow_started", self._current_node)

    def _execute_node(self, node: Node) -> str | None:
        context = WorkflowContext(self._require_context(), node)
        if node.kind is NodeKind.END:
            return None
        if node.kind is NodeKind.PARALLEL:
            self._execute_parallel(node)
            next_name = node.metadata.get("next")
            return next_name if isinstance(next_name, str) else None
        value = self._run(node, context)
        self._output = value
        self._require_context().variables[node.name] = value
        if node.kind is NodeKind.CONDITION or node.kind is NodeKind.LOOP:
            return self._boolean_successor(node, bool(value))
        if node.kind is NodeKind.BRANCH:
            return self._branch_successor(node, value)
        return self._next(node)

    def _execute_parallel(self, node: Node) -> None:
        for name in node.successors:
            branch = self._nodes[name]
            if branch.kind not in {NodeKind.TASK, NodeKind.RETRY}:
                raise ValueError(
                    "Reference parallel branches must be task or retry nodes."
                )
            self._emit("parallel_branch_started", branch.name)
            value = self._run(branch, WorkflowContext(self._require_context(), branch))
            self._require_context().variables[branch.name] = value
            self._output = value
            self._emit("parallel_branch_completed", branch.name)

    def _run(self, node: Node, context: WorkflowContext) -> object | None:
        attempts = 1
        if node.kind is NodeKind.RETRY:
            attempts_value = node.metadata.get("attempts", 1)
            if not isinstance(attempts_value, int):
                raise ValueError("Retry node attempts must be an integer.")
            attempts = attempts_value
        if attempts < 1:
            raise ValueError("Retry node attempts must be at least one.")
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                if callable(node.handler):
                    handler = cast(
                        Callable[[WorkflowContext], object | None], node.handler
                    )
                    return handler(context)
                return node.handler
            except Exception as error:
                last_error = error
                self._emit("node_retry", node.name, {"attempt": attempt + 1})
        assert last_error is not None
        raise last_error

    @staticmethod
    def _next(node: Node) -> str | None:
        return node.successors[0] if node.successors else None

    @staticmethod
    def _boolean_successor(node: Node, value: bool) -> str | None:
        index = 0 if value else 1
        return node.successors[index] if len(node.successors) > index else None

    @staticmethod
    def _branch_successor(node: Node, value: object) -> str | None:
        if isinstance(value, str) and value in node.successors:
            return value
        if isinstance(value, int) and 0 <= value < len(node.successors):
            return node.successors[value]
        return WorkflowRuntime._boolean_successor(node, bool(value))

    def _cancelled_or_timed_out(self) -> bool:
        context = self._require_context()
        if context.cancellation.is_set():
            self._state = WorkflowState.CANCELLED
            self._emit("workflow_cancelled", self._current_node)
            return True
        if (
            context.timeout_seconds is not None
            and self._started_at is not None
            and self._clock() - self._started_at >= context.timeout_seconds
        ):
            self._state = WorkflowState.TIMED_OUT
            self._emit("workflow_timed_out", self._current_node)
            return True
        return False

    def _fail(self, error: Exception, node: Node | None = None) -> None:
        self._error = error
        self._state = WorkflowState.FAILED
        self._emit("workflow_failed", node.name if node else self._current_node)
        for hook in self._hooks:
            try:
                hook.on_error(node, error)
            except Exception:
                continue

    def _notify(self, method: str, node: Node | None = None) -> None:
        for hook in self._hooks:
            try:
                callback = getattr(hook, method)
                callback() if node is None else callback(node)
            except Exception:
                continue

    def _emit(
        self,
        name: str,
        node: str | None = None,
        detail: Mapping[str, object] | None = None,
    ) -> None:
        self._events.append(ExecutionEvent(name, node, detail=detail or {}))

    def _require_context(self) -> ExecutionContext:
        assert self._context is not None
        return self._context

    def _result(self) -> WorkflowResult:
        variables = self._context.variables if self._context is not None else {}
        return WorkflowResult(
            self._state,
            self._output,
            variables,
            tuple(self._events),
            self._error,
        )


@dataclass(frozen=True, slots=True)
class EchoTask:
    """Reference task returning a fixed value or the explicit input variable."""

    value: object | None = None

    def __call__(self, context: WorkflowContext) -> object | None:
        """Return the configured value without external execution."""
        return context.variables.get("input") if self.value is None else self.value


@dataclass(frozen=True, slots=True)
class DelayTask:
    """Reference delay marker that records duration without sleeping."""

    duration_seconds: float = 0.0

    def __call__(self, context: WorkflowContext) -> float:
        """Return the configured local duration marker without waiting."""
        del context
        return self.duration_seconds


@dataclass(frozen=True, slots=True)
class ConditionTask:
    """Reference condition task with a deterministic caller-supplied predicate."""

    predicate: Callable[[WorkflowContext], bool]

    def __call__(self, context: WorkflowContext) -> bool:
        """Evaluate the local predicate without selecting a provider."""
        return self.predicate(context)


@dataclass(frozen=True, slots=True)
class ReferenceMemoryTask:
    """Store one value through an explicitly injected reference-memory object."""

    key: str
    value: object

    def __call__(self, context: WorkflowContext) -> object:
        """Store a local record when the context exposes a compatible memory API."""
        if context.execution.memory is None:
            raise RuntimeError("Memory task requires an explicit memory dependency.")
        from ..memory import MemoryRecord

        memory = context.execution.memory
        record = MemoryRecord(self.key, self.value)
        store = getattr(memory, "store", None)
        if callable(store):
            store(record)
            return self.value
        put = getattr(memory, "put", None)
        if not callable(put):
            raise RuntimeError("Memory task requires a compatible memory API.")
        put(record)
        return self.value
