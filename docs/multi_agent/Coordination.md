# Coordination

Coordination orders dependency graphs, prioritizes ready tasks, filters agents
by capabilities and readiness, and balances assignments by utilization.
Cycles are synchronized, audited, isolated, and counted. Missing capabilities
fail closed so callers can escalate, retry, or select a fallback.
