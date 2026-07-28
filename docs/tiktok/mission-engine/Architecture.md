# TikTok Autonomous Mission Engine Architecture

The mission engine is a local, single-user control-plane coordinator for missions
approved by the TikTok Autonomous Operation Center. It owns queue state,
allocation references, checkpoints, health aggregation, recovery coordination,
analytics, and audit records. It does not own platform execution.

Every dispatch uses bounded ports to the existing Autonomous Operation Center,
Task Scheduler, Automation Engine, Workflow Center, Execution Engine, Runtime
Manager, Resource Center, Browser Cluster, Device Center, and Risk Control
Center. The execution-capable services receive reference-only delegation; the
mission engine creates no browser, device, workflow, automation, or execution
infrastructure.

Tenant and workspace are carried on every mission, checkpoint, and audit entry.
RBAC and current approval are enforced before mutation. Secret-like payload keys
are rejected. Any unresolved TikTok restriction or challenge stops dispatch and
recovery.
