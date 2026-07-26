# Enterprise Workflow Platform

The package provides the TKAI V3.1 workflow domain, visual-designer contracts,
bounded execution, history, scheduling, approvals, forms, conditions, variables,
templates, connectors, dashboard projections, metrics, and HTTP route adapters.

All stores enforce tenant/workspace scope. Secret expressions return opaque
references and never expose secret values. The engine has bounded retry, timeout,
execution-count and connector limits, and records checkpoints and execution
history. External integrations are interfaces or deterministic in-memory
references only.
