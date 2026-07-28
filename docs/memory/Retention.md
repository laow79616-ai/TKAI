# Memory Retention

Retention policies provide default TTL, expiration handling, archive behavior,
priority-aware cleanup, and compaction. Cleanup only considers the caller's
tenant/workspace. Compaction retains the newest duplicate content within a
namespace and archives older copies. Operators should schedule cleanup and
select durable archive/storage adapters for production.
