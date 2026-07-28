# Memory Performance

The bounded LRU cache records hits, misses, size, limit, and evictions.
Retrieval applies scope filters before scoring and bounds output with top-K.
Chunk and metadata compression use zlib and compact JSON to estimate optimized
storage. Production deployments should monitor all `memory_*` counters, size
cache limits per pod, use a shared cache when needed, and benchmark candidate
index/storage adapters with representative tenant workloads.
