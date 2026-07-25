# Policy Engine

The optional `tkai.policy` package provides one explicit, provider-neutral
policy pipeline.  It does not automatically alter `AIClient`,
`ProviderManager`, or Provider Runtime behaviour.

## Interface and lifecycle

Each policy implements `name()`, `priority()`, `enabled()`, `evaluate()`,
`apply()`, and `shutdown()`.  Policies run in descending priority and then
ascending name order.  Evaluation rejection, disabled policies, and exceptions
produce explicit execution outcomes; an exception is isolated so later policies
still run.

## Pipeline stages

`PolicyStage` supports `before_request`, `before_routing`, `before_provider`,
`after_provider`, and `after_response`.  Application code explicitly creates a
`PolicyContext` or uses `PolicyManager.pipeline.run(stage, data)`.  No stage is
automatically wired into existing V1.1 execution paths.

## Compatibility adapters

`RoutingPolicyAdapter`, `BreakerPolicyAdapter`, `RateLimitPolicyAdapter`,
`CachePolicyAdapter`, and `PluginPolicyAdapter` expose existing V1.1 policy-like
objects through the new contract without modifying the wrapped object or
enabling any service by default.

## Observability, Doctor, and CLI

The engine optionally publishes `PolicyExecuted`, `PolicySkipped`, and
`PolicyFailed` through the shared EventBus.  `DoctorService` can inspect a
supplied `PolicyManager` without evaluating policies.  `tkai ai policy` renders
registered policy metadata in text or JSON form.
