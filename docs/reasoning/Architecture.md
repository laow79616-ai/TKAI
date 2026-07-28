# Enterprise AI Reasoning Engine Architecture

The reasoning engine is an additive, tenant-scoped service beside the memory engine
and orchestrator. `EnterpriseAIReasoningEngine` owns session lifecycle and composes
planning, decision, validation, simulation, optimization, policy, and explanation
domains. The FastAPI-compatible adapter exposes `/reasoning` resources, the
dashboard consumes the same API, and metrics join the platform Prometheus endpoint.

Sessions move through `created`, `prepared`, `running`, `validated`, `completed`,
`failed`, `cancelled`, and `archived`. Explicit transition rules prevent invalid
state changes. Artifacts remain associated with a session and are returned by the
explanation view without exposing internal chain-of-thought.
