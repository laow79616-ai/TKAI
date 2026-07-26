"""Enterprise agent lifecycle service built on the existing workflow runtime."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from threading import RLock
from time import monotonic
from typing import Any

from tkai.workflow import WorkflowDefinition, WorkflowEngine, WorkflowRuntime

from ..definition import AgentDefinition
from ..execution import AgentRun
from ..memory import ShortMemory
from ..models import AgentEvent, AgentStatus, RunMetrics
from ..tools import ToolRegistry
from .audit import AgentAuditAction, AgentAuditLog
from .metrics import AgentMetrics

_TRANSITIONS: dict[AgentStatus, frozenset[AgentStatus]] = {
    AgentStatus.DRAFT: frozenset({AgentStatus.CREATED, AgentStatus.ARCHIVED}),
    AgentStatus.CREATED: frozenset({AgentStatus.READY, AgentStatus.ARCHIVED}),
    AgentStatus.READY: frozenset({AgentStatus.RUNNING, AgentStatus.ARCHIVED}),
    AgentStatus.RUNNING: frozenset(
        {
            AgentStatus.PAUSED,
            AgentStatus.COMPLETED,
            AgentStatus.FAILED,
            AgentStatus.CANCELLED,
        }
    ),
    AgentStatus.PAUSED: frozenset(
        {AgentStatus.RUNNING, AgentStatus.CANCELLED}
    ),
    AgentStatus.COMPLETED: frozenset({AgentStatus.ARCHIVED}),
    AgentStatus.FAILED: frozenset({AgentStatus.ARCHIVED}),
    AgentStatus.CANCELLED: frozenset({AgentStatus.ARCHIVED}),
    AgentStatus.ARCHIVED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class AgentRecord:
    definition: AgentDefinition
    status: AgentStatus = AgentStatus.DRAFT

    def to_dict(self) -> dict[str, Any]:
        return {**self.definition.to_dict(), "status": self.status.value}


class AgentRuntime:
    """Coordinates agent state while delegating all scheduling to WorkflowEngine."""

    def __init__(
        self,
        *,
        workflow_engine: WorkflowEngine | None = None,
        clock: Callable[[], str] = lambda: "local",
        run_id_factory: Callable[[], str] | None = None,
        metrics: AgentMetrics | None = None,
        audit: AgentAuditLog | None = None,
        memory: ShortMemory | None = None,
        tools: ToolRegistry | None = None,
    ) -> None:
        self.workflow_engine = workflow_engine or WorkflowEngine()
        self.clock = clock
        self.run_id_factory = run_id_factory or self._next_run_id
        self.metrics = metrics or AgentMetrics()
        self.audit = audit or AgentAuditLog()
        self.memory = memory or ShortMemory()
        self.tools = tools or ToolRegistry()
        self._agents: dict[str, AgentRecord] = {}
        self._runs: dict[str, AgentRun] = {}
        self._workflow_runs: dict[str, WorkflowRuntime] = {}
        self._sequence = 0
        self._lock = RLock()

    def _next_run_id(self) -> str:
        self._sequence += 1
        return f"run-{self._sequence}"

    def create(
        self, definition: AgentDefinition, *, actor: str | None = None
    ) -> AgentRecord:
        with self._lock:
            if definition.agent_id in self._agents:
                raise ValueError(f"Agent '{definition.agent_id}' already exists.")
            record = AgentRecord(definition, AgentStatus.DRAFT)
            self._agents[definition.agent_id] = record
            self.audit.record(
                AgentAuditAction.CREATE, definition.agent_id, self.clock(), actor
            )
            return record

    def list_agents(self) -> tuple[AgentRecord, ...]:
        with self._lock:
            return tuple(self._agents[key] for key in sorted(self._agents))

    def get_agent(self, agent_id: str) -> AgentRecord:
        with self._lock:
            try:
                return self._agents[agent_id]
            except KeyError as error:
                raise KeyError(f"Unknown agent '{agent_id}'.") from error

    def transition(self, agent_id: str, status: AgentStatus) -> AgentRecord:
        with self._lock:
            current = self.get_agent(agent_id)
            if status not in _TRANSITIONS[current.status]:
                raise ValueError(
                    f"Illegal agent transition: {current.status.value} -> "
                    f"{status.value}"
                )
            updated = replace(current, status=status)
            self._agents[agent_id] = updated
            return updated

    def prepare(self, agent_id: str) -> AgentRecord:
        current = self.get_agent(agent_id)
        if current.status is AgentStatus.DRAFT:
            self.transition(agent_id, AgentStatus.CREATED)
        return self.transition(agent_id, AgentStatus.READY)

    def archive(self, agent_id: str) -> AgentRecord:
        """Archive an inactive definition."""
        return self.transition(agent_id, AgentStatus.ARCHIVED)

    def start_run(
        self,
        agent_id: str,
        workspace: str,
        inputs: Mapping[str, Any],
        *,
        workflow: WorkflowDefinition | None = None,
        actor: str | None = None,
    ) -> AgentRun:
        with self._lock:
            agent = self.get_agent(agent_id)
            if agent.status is not AgentStatus.READY:
                raise ValueError("Agent must be ready before it can run.")
            run_id = self.run_id_factory()
            timestamp = self.clock()
            event = AgentEvent(1, "run", AgentStatus.RUNNING, timestamp)
            run = AgentRun(
                run_id,
                agent_id,
                workspace,
                inputs,
                status=AgentStatus.RUNNING,
                events=(event,),
            )
            self._runs[run_id] = run
            self.transition(agent_id, AgentStatus.RUNNING)
            if workflow is not None:
                self._workflow_runs[run_id] = self.workflow_engine.create_runtime(
                    workflow, dict(inputs)
                )
            self.metrics.increment("agent_runs_total")
            self.audit.record(AgentAuditAction.RUN, run_id, timestamp, actor)
            return run

    def complete(
        self,
        run_id: str,
        outputs: Mapping[str, Any],
        *,
        duration_seconds: float = 0.0,
    ) -> AgentRun:
        return self._finish(
            run_id, AgentStatus.COMPLETED, outputs, duration_seconds
        )

    def fail(self, run_id: str, *, duration_seconds: float = 0.0) -> AgentRun:
        return self._finish(run_id, AgentStatus.FAILED, {}, duration_seconds)

    def pause(self, run_id: str, *, actor: str | None = None) -> AgentRun:
        workflow = self._workflow_runs.get(run_id)
        if workflow is not None:
            self.workflow_engine.pause(workflow, run_id)
        return self._control(run_id, AgentStatus.PAUSED, AgentAuditAction.PAUSE, actor)

    def resume(self, run_id: str, *, actor: str | None = None) -> AgentRun:
        workflow = self._workflow_runs.get(run_id)
        if workflow is not None:
            workflow.resume()
        return self._control(
            run_id, AgentStatus.RUNNING, AgentAuditAction.RESUME, actor
        )

    def cancel(self, run_id: str, *, actor: str | None = None) -> AgentRun:
        workflow = self._workflow_runs.get(run_id)
        if workflow is not None:
            self.workflow_engine.cancel(workflow, run_id)
        run = self._control(
            run_id, AgentStatus.CANCELLED, AgentAuditAction.CANCEL, actor
        )
        self.metrics.increment("agent_cancelled_total")
        return run

    def delete_run(self, run_id: str, *, actor: str | None = None) -> None:
        with self._lock:
            run = self.get_run(run_id)
            if run.status in {AgentStatus.RUNNING, AgentStatus.PAUSED}:
                self.cancel(run_id, actor=actor)
            self._runs.pop(run_id)
            self._workflow_runs.pop(run_id, None)
            self.audit.record(
                AgentAuditAction.DELETE, run_id, self.clock(), actor
            )

    def get_run(self, run_id: str) -> AgentRun:
        with self._lock:
            try:
                return self._runs[run_id]
            except KeyError as error:
                raise KeyError(f"Unknown agent run '{run_id}'.") from error

    def list_runs(self) -> tuple[AgentRun, ...]:
        with self._lock:
            return tuple(self._runs[key] for key in sorted(self._runs))

    def invoke_tool(
        self, run_id: str, name: str, payload: Mapping[str, Any]
    ) -> Any:
        """Invoke a registered tool under definition permissions and run limits."""
        with self._lock:
            run = self.get_run(run_id)
            if run.status is not AgentStatus.RUNNING:
                raise ValueError("Tools can only be called by a running agent.")
            definition = self.get_agent(run.agent_id).definition
            if name not in definition.tools:
                raise PermissionError(f"Tool '{name}' is not assigned to this agent.")
            if run.metrics.tool_calls >= definition.limits.max_tool_calls:
                raise ValueError("Maximum tool calls exceeded.")
            tool = self.tools.get(name, definition.permissions)
        self.metrics.increment("tool_calls_total")
        attempts = 0
        started = monotonic()
        try:
            while True:
                attempts += 1
                try:
                    result = tool.handler(payload)
                    if monotonic() - started > tool.definition.timeout_seconds:
                        raise TimeoutError(f"Tool '{name}' exceeded its timeout.")
                    break
                except Exception:
                    if attempts >= tool.definition.retry.attempts:
                        raise
        except Exception:
            self._update_tool_metrics(run_id, failed=True)
            raise
        self._update_tool_metrics(run_id, failed=False)
        return result

    def _update_tool_metrics(self, run_id: str, *, failed: bool) -> None:
        with self._lock:
            run = self.get_run(run_id)
            metrics = replace(
                run.metrics,
                tool_calls=run.metrics.tool_calls + 1,
                tool_failures=run.metrics.tool_failures + int(failed),
            )
            self._runs[run_id] = run.evolve(metrics=metrics)
            if failed:
                self.metrics.increment("tool_failures_total")

    def _control(
        self,
        run_id: str,
        target: AgentStatus,
        action: AgentAuditAction,
        actor: str | None,
    ) -> AgentRun:
        with self._lock:
            run = self.get_run(run_id)
            if target not in _TRANSITIONS[run.status]:
                raise ValueError(
                    f"Illegal run transition: {run.status.value} -> {target.value}"
                )
            timestamp = self.clock()
            event = AgentEvent(
                len(run.events) + 1, action.value, target, timestamp
            )
            updated = run.evolve(status=target, events=run.events + (event,))
            self._runs[run_id] = updated
            self.transition(run.agent_id, target)
            self.audit.record(action, run_id, timestamp, actor)
            return updated

    def _finish(
        self,
        run_id: str,
        status: AgentStatus,
        outputs: Mapping[str, Any],
        duration_seconds: float,
    ) -> AgentRun:
        started = monotonic()
        with self._lock:
            run = self.get_run(run_id)
            if status not in _TRANSITIONS[run.status]:
                raise ValueError("Run is not active.")
            duration = duration_seconds or max(0.0, monotonic() - started)
            event = AgentEvent(
                len(run.events) + 1, status.value, status, self.clock()
            )
            updated = run.evolve(
                outputs=outputs,
                status=status,
                events=run.events + (event,),
                metrics=RunMetrics(duration_seconds=duration),
            )
            self._runs[run_id] = updated
            self.transition(run.agent_id, status)
            self.metrics.increment(
                "agent_success_total"
                if status is AgentStatus.COMPLETED
                else "agent_failed_total"
            )
            self.metrics.observe_duration(duration)
            return updated


__all__ = ("AgentMetrics", "AgentRecord", "AgentRuntime")
