"""TTL expiration, archiving, cleanup, and compaction policies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..models import MemoryObject


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    default_ttl: int | None = None
    archive_expired: bool = True
    cleanup_priority_below: int = 101


class RetentionManager:
    def __init__(self, policy: RetentionPolicy | None = None) -> None:
        self.policy = policy or RetentionPolicy()

    def ttl_for(self, requested: int | None) -> int | None:
        ttl = requested if requested is not None else self.policy.default_ttl
        if ttl is not None and ttl < 0:
            raise ValueError("TTL cannot be negative.")
        return ttl

    def expired(self, memory: MemoryObject, now: datetime | None = None) -> bool:
        return memory.expired(now)

    def compact(self, memories: list[MemoryObject]) -> list[MemoryObject]:
        latest: dict[tuple[str, str, str, str], MemoryObject] = {}
        for memory in memories:
            key = (memory.tenant, memory.workspace, memory.namespace, memory.content)
            current = latest.get(key)
            if current is None or memory.updated > current.updated:
                latest[key] = memory
        return list(latest.values())
