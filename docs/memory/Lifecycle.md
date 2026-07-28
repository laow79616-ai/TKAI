# Memory Lifecycle

Memories move through created, updated, indexed, retrieved, expired, archived,
and deleted states. Creation validates scope and secret references before
indexing and cache population. Updates refresh the timestamp and index.
Retrieval checks TTL. Expiration removes active index/cache entries and,
according to policy, archives the object. Explicit deletion is final in the
reference store and emits an audit event.
