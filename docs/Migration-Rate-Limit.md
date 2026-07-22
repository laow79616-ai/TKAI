# Rate Limiter migration note

Rate Limiter is an optional V1.1 capability. It does not change V1 public APIs and does not automatically enforce quotas in `ProviderManager`. Applications opt in by registering `RateLimitSnapshot` values with `RateLimitManager` and, if routing filtering is wanted, explicitly using `RateLimitAwareStrategy`. State is not persisted or shared between processes.
