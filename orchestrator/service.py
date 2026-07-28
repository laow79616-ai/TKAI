"""Enterprise orchestrator facade."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from .checkpoints import CheckpointStore
from .coordinator import Coordinator
from .events import EventBus
from .executor import Executor
from .metrics import OrchestratorMetrics
from .models import Execution, ExecutionPlan, ExecutionState, RouteType, Scope
from .planner import Planner
from .policies import PolicySet
from .queue import ExecutionQueue
from .recovery import RecoveryManager
from .router import Handler, Router
from .scheduler import Scheduler
from .security import OrchestratorSecurity


class EnterpriseAIOrchestrator:
    def __init__(
        self, *, policies: PolicySet | None = None, execution_limit: int = 100
    ) -> None:
        self.policies = policies or PolicySet()
        self.metrics = OrchestratorMetrics()
        self.security = OrchestratorSecurity(execution_limit)
        self.planner = Planner()
        self.router = Router()
        self.queue = ExecutionQueue()
        self.scheduler = Scheduler(self.queue)
        self.coordinator = Coordinator(
            self.policies.concurrency.maximum,
            self.policies.concurrency.maximum,
        )
        self.events = EventBus()
        self.checkpoints = CheckpointStore()
        self.recovery = RecoveryManager(self.checkpoints)
        self.executor = Executor(
            self.router,
            self.checkpoints,
            self.events,
            self.metrics,
            self.policies,
        )
        self._plans: dict[str, ExecutionPlan] = {}
        self._executions: dict[str, Execution] = {}

    def register(self, route: RouteType, handler: Handler) -> None:
        self.router.register(route, handler)

    def create_plan(self, payload: dict[str, Any], scope: Scope) -> ExecutionPlan:
        self.security.require(scope, "plan:create")
        self.security.validate_secrets(payload)
        plan = self.planner.create(payload, scope)
        self._plans[plan.id] = plan
        self.metrics.increment("execution_plans_total")
        return plan

    def list_plans(self, scope: Scope) -> tuple[ExecutionPlan, ...]:
        return tuple(p for p in self._plans.values() if p.scope.tenant == scope.tenant)

    def submit(
        self, plan_id: str, scope: Scope, *, delay_seconds: float = 0
    ) -> Execution:
        self.security.require(scope, "execution:run")
        plan = self._plan(plan_id, scope)
        active = sum(
            item.scope.tenant == scope.tenant
            and item.state in {ExecutionState.QUEUED, ExecutionState.RUNNING}
            for item in self._executions.values()
        )
        if active >= self.security.execution_limit:
            raise RuntimeError("Execution limit reached.")
        execution = Execution(str(uuid4()), plan.id, scope, ExecutionState.QUEUED)
        self._executions[execution.id] = execution
        self.scheduler.schedule(execution.id, plan.priority.value, delay_seconds)
        self.metrics.increment("execution_total")
        self.metrics.set("queue_depth", self.queue.depth)
        return execution

    def execute(
        self, execution_id: str, scope: Scope, context: dict[str, Any] | None = None
    ) -> Execution:
        execution = self._execution(execution_id, scope)
        plan = self._plan(execution.plan_id, scope)
        self.coordinator.acquire(scope.tenant)
        try:
            return self.executor.run(plan, execution, context or {})
        except Exception as error:
            execution.state = ExecutionState.FAILED
            execution.error = str(error)
            self.metrics.increment("execution_failed_total")
            self.queue.dead_letter(execution.id)
            self.events.publish(
                "execution.failed", execution_id=execution.id, error=str(error)
            )
            return execution
        finally:
            self.coordinator.release(scope.tenant)

    def cancel(self, execution_id: str, scope: Scope) -> Execution:
        execution = self._execution(execution_id, scope)
        execution.cancelled = True
        if execution.state is not ExecutionState.RUNNING:
            execution.state = ExecutionState.CANCELLED
        self.security.record(scope, "execution:cancel", execution_id=execution.id)
        return execution

    def resume(self, execution_id: str, scope: Scope, checkpoint_id: str) -> Execution:
        execution = self._execution(execution_id, scope)
        step = self.recovery.restore(execution, checkpoint_id)
        self.metrics.increment("recovery_total")
        return self.executor.run(
            self._plan(execution.plan_id, scope), execution, {}, start_at=step
        )

    def rollback(self, execution_id: str, scope: Scope) -> Execution:
        execution = self.recovery.rollback(self._execution(execution_id, scope))
        self.metrics.increment("recovery_total")
        self.security.record(scope, "execution:rollback", execution_id=execution.id)
        return execution

    def list_executions(self, scope: Scope) -> tuple[Execution, ...]:
        return tuple(
            item
            for item in self._executions.values()
            if item.scope.tenant == scope.tenant
        )

    def dashboard(self, scope: Scope) -> dict[str, Any]:
        executions = self.list_executions(scope)
        return {
            "sections": (
                "Execution Plans",
                "Queues",
                "Executions",
                "Failures",
                "Retries",
                "Performance",
            ),
            "plans": len(self.list_plans(scope)),
            "queues": {
                "depth": self.queue.depth,
                "dead_letter": len(self.queue.dead_letters),
            },
            "executions": len(executions),
            "failures": sum(e.state is ExecutionState.FAILED for e in executions),
            "retries": self.metrics.snapshot()["execution_retry_total"],
            "performance": self.coordinator.snapshot(),
        }

    def _plan(self, plan_id: str, scope: Scope) -> ExecutionPlan:
        plan = self._plans[plan_id]
        self.security.isolate(plan.scope, scope)
        return plan

    def _execution(self, execution_id: str, scope: Scope) -> Execution:
        execution = self._executions[execution_id]
        self.security.isolate(execution.scope, scope)
        return execution
