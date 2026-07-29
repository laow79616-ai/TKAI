"""Resource, execution, cost, and latency optimization."""

from __future__ import annotations

from ..models import ExecutionPlan, OptimizationResult


class Optimizer:
    def optimize(
        self,
        plan: ExecutionPlan,
        resources: dict[str, float],
        *,
        cost_per_unit: float = 1.0,
        latency_per_task: float = 1.0,
    ) -> OptimizationResult:
        normalized = {key: max(0.0, float(value)) for key, value in resources.items()}
        total = sum(normalized.values())
        allocation = (
            {key: value / total for key, value in normalized.items()}
            if total
            else normalized
        )
        task_count = len(plan.subtasks)
        return OptimizationResult(
            resource=allocation,
            execution=plan.execution_order,
            estimated_cost=total * max(0.0, cost_per_unit),
            estimated_latency=task_count * max(0.0, latency_per_task),
        )
