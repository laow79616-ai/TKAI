# Cost-aware Routing migration note

Routing Foundation is an optional V1.1 subsystem. Existing V1 AIClient, ProviderManager, Runtime, Health, Circuit Breaker, Observability, and Configuration APIs are unchanged. Applications may opt in by registering `ProviderMetadata` with a `RoutingManager`; no existing configuration or API call needs migration.
