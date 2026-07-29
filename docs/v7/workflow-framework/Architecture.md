# V7 Unified Workflow Orchestration Framework

The framework is an internal coordination layer for immutable workflow metadata.
It registers definitions, validates references and isolation boundaries, builds
deterministic dependency-ordered plans, records lifecycle and audit history, and
coordinates reference-only recovery plans.

It has no worker, dispatcher, action adapter, browser integration, or TikTok API
client. `orchestrate()` is an alias for planning and never executes a workflow.
Existing V6 workflow and TikTok modules remain independent and unchanged.

Immutable contracts flow into `WorkflowRegistry`, validation, and topological
planning. Read-only snapshots feed GET APIs and the dashboard. Metrics, structured
logs, trace hooks, and audit history observe metadata operations.
