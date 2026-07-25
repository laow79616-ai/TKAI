# Cache Framework

TKAI Cache is an optional, process-local caching foundation. It does not automatically change Runtime, AIClient, or ProviderManager behavior.

`CacheEntry` is immutable and records a key, optional provider/model metadata, UTC creation/expiry timestamps, TTL, and access metadata. `CacheBackend` defines get, set, delete, contains, clear, size, statistics, and memory-estimate behavior. The default `InMemoryBackend` is thread-safe and evicts expired entries on read.

`CacheKeyBuilder` hashes canonical provider, model, prompt, parameters, and version data, so prompts do not appear directly in keys. `CachePolicy`, `NoCache`, `ReadThrough`, and `WriteThrough` declare optional call-path behavior. `CacheManager.get_or_set()` is an explicit read-through helper; it is not wired into Runtime by default.

Cache hit, miss, expiration, and eviction events reuse the shared Observability EventBus. Existing Metrics, Logger, and Trace subscribers can observe those events without a separate exporter.

```console
tkai ai cache
tkai ai cache --json
```

Doctor reports backend registry, entry count, estimated memory, and hit/miss ratios without displaying cached values. The current implementation has no Redis backend, distributed cache, warming, prefetching, multilayer cache, or persistence.
