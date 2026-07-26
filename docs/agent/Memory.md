# Agent Memory

`ShortMemory` is a bounded, thread-safe, in-process store partitioned by an
explicit `MemoryNamespace`. `RetentionPolicy.max_items` evicts the oldest key
within each namespace. `LongMemory` is a protocol for caller-provided durable
storage; this foundation does not choose or connect to a database.

