# Enterprise Agent Runtime Architecture

TKAI V2.2 adds `tkai.agent` as an additive, local-first foundation. Immutable
definitions and run records sit above explicit memory, tool, coordination,
audit, and metrics services. `AgentRuntime` composes the existing
`tkai.workflow.WorkflowEngine`; it does not implement another scheduler,
executor, checkpoint format, or workflow runtime.

The package has no import-time network, filesystem, container, or background
worker behavior. Services are instance-scoped and safe to inject into the
existing API and Docker application.

