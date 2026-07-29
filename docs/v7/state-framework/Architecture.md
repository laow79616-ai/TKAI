# V7 Unified State Management Architecture

The framework is an opt-in, in-process control plane under
`tkai.v7.state_framework`. It standardizes immutable state contracts, explicit
registry operations, deterministic lifecycle transitions, reference-only
snapshots, unified history, consistency checks, observability, security, and
non-mutating recovery simulation.

It does not start workers, perform network access, mutate runtime components,
alter V6 imports, or change TikTok business behavior. Persistence is an injected
protocol. The built-in memory adapter is intended for tests and local control
planes.

The composition root is `StateFramework`. APIs and the dashboard expose
read-only projections. All mutations require direct method calls by an owning
component.
