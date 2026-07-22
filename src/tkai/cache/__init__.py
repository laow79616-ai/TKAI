"""Optional pluggable local cache framework with a default memory backend."""

from .backend import CacheBackend
from .errors import CacheBackendNotFoundError, CacheError
from .events import CacheEvent, CacheEvicted, CacheExpired, CacheHit, CacheMiss
from .keys import CacheKeyBuilder
from .manager import CacheManager
from .memory import InMemoryBackend
from .models import CacheEntry, CacheStatistics
from .policy import CachePolicy, NoCache, ReadThrough, WriteThrough
from .registry import CacheRegistry

__all__ = (
    "CacheBackend",
    "CacheBackendNotFoundError",
    "CacheEntry",
    "CacheError",
    "CacheEvent",
    "CacheEvicted",
    "CacheExpired",
    "CacheHit",
    "CacheKeyBuilder",
    "CacheManager",
    "CacheMiss",
    "CachePolicy",
    "CacheRegistry",
    "CacheStatistics",
    "InMemoryBackend",
    "NoCache",
    "ReadThrough",
    "WriteThrough",
)
