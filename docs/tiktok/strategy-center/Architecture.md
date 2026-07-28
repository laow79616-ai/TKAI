# Architecture

The Strategy Center is a bounded advisory domain. It reads existing systems
through `StrategyInputPort`, evaluates snapshot evidence locally, and emits
`StrategyRecommendation` records. The only outward integration is
`StrategyHandoffPort.accept_reference`; it cannot dispatch a mission or mutate
an upstream module. Scope, RBAC, approvals, audit, metrics, and safe-reference
rules reuse repository conventions.
