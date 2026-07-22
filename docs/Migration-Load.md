# Load subsystem migration note

Load is an optional V1.1 capability. It does not change V1 public APIs, does not automatically take over ProviderManager routing, and does not alter `CostAwareStrategy`. Applications opt in by attaching `LoadManager` to an existing EventBus and configuring a `RoutingManager` with `LoadAwareStrategy`. Local snapshots are not persisted or shared across processes.
