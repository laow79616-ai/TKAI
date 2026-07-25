# ADR 007: Cache Framework Foundation

## Status

Accepted.

## Decision

Use a backend interface, immutable cache entries, deterministic key builder, policy types, and a thread-safe in-memory backend. Publish cache lifecycle events through the existing EventBus. Keep Runtime integration explicit through `CacheManager.get_or_set()`.

## Rationale

The backend interface permits future Redis or other storage without changing callers. Key building protects prompts by hashing canonical input. Policy types make caching intent visible. An in-memory backend is dependency-free and testable. Explicit integration preserves compatibility with existing Runtime and ProviderManager paths.

## Consequences

Cache state is local and ephemeral. There is no distributed cache, warming, prefetching, multilayer hierarchy, or automatic ProviderManager takeover.
