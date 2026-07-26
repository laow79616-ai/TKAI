"""Core memory object and query models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class MemoryType(str, Enum):
    WORKING = "working"
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    SESSION = "session"
    SHARED = "shared"


class LifecycleState(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    INDEXED = "indexed"
    RETRIEVED = "retrieved"
    EXPIRED = "expired"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass(frozen=True, slots=True)
class MemoryScope:
    tenant: str
    workspace: str
    owner: str

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.owner:
            raise ValueError("Tenant, workspace, and owner are required.")


@dataclass(slots=True)
class MemoryObject:
    id: str
    namespace: str
    tenant: str
    workspace: str
    owner: str
    type: MemoryType
    source: str
    content: str
    created: datetime
    updated: datetime
    ttl: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    priority: int = 50
    state: LifecycleState = LifecycleState.CREATED

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["type"] = self.type.value
        value["state"] = self.state.value
        value["created"] = self.created.isoformat()
        value["updated"] = self.updated.isoformat()
        return value

    @property
    def scope(self) -> MemoryScope:
        return MemoryScope(self.tenant, self.workspace, self.owner)

    def expired(self, now: datetime | None = None) -> bool:
        if self.ttl is None:
            return False
        current = now or datetime.now(UTC)
        return (current - self.updated).total_seconds() >= self.ttl


@dataclass(frozen=True, slots=True)
class SearchQuery:
    text: str
    mode: str = "hybrid"
    namespace: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    top_k: int = 10
    threshold: float = 0.0

    def __post_init__(self) -> None:
        if self.mode not in {"similarity", "keyword", "hybrid"}:
            raise ValueError("Search mode must be similarity, keyword, or hybrid.")
        if self.top_k < 1:
            raise ValueError("Top-K must be positive.")
        if not 0 <= self.threshold <= 1:
            raise ValueError("Threshold must be between zero and one.")


@dataclass(frozen=True, slots=True)
class SearchResult:
    memory: MemoryObject
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {"memory": self.memory.to_dict(), "score": self.score}
