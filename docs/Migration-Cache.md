# Cache migration note

Cache Framework is an optional V1.1 addition. Existing V1 public APIs and behavior are unchanged. Applications opt in by using `CacheManager` or an explicit read-through call path; cache is not enabled automatically and is not persistent across processes.
