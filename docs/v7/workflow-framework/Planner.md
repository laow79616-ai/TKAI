# Planner and Orchestration

Planning validates the definition, dependencies, constraints, versions, state
references, scope, priority, and window. It produces a deterministic topological
order using IDs as tie-breakers. Plans are bounded by `max_plan_size`, immutable,
and `reference_only`. Planning does not enqueue, schedule, dispatch, or execute.
