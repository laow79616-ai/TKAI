# Adaptive Routing migration note

Adaptive routing is a new optional capability. V1.1 and V1.2 AIClient,
ProviderManager, Runtime, and legacy Routing APIs retain their existing behavior.
No configuration migration is required.

Adaptive scoring only takes effect when an application explicitly creates an
`AdaptiveRoutingManager`, `AdaptiveRoutingRuntimeAdapter`, or
`AdaptiveRoutingPolicyAdapter` and invokes or registers it.
