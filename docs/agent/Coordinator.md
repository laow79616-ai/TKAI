# Multi-Agent Coordinator

The coordinator supports Planner, Research, Coder, Reviewer, Executor, and
Support roles. Delegation is bounded by maximum depth and maximum agents.
Execution is injected by the caller, aggregation preserves delegation order,
and cooperative cancellation stops further delegation. The coordinator does
not create threads, processes, schedulers, or a second runtime.

