"""Core enterprise knowledge value objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class KnowledgeStatus(str, Enum):
    DRAFT = "draft"
    INDEXING = "indexing"
    READY = "ready"
    PAUSED = "paused"
    FAILED = "failed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Visibility(str, Enum):
    PRIVATE = "private"
    TEAM = "team"
    ORGANIZATION = "organization"
    TENANT = "tenant"
    PUBLIC = "public"


class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    MANAGE = "manage"
    SHARE = "share"
    EXPORT = "export"


@dataclass(frozen=True, slots=True)
class Scope:
    tenant: str
    workspace: str
    namespace: str

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.namespace)):
            raise ValueError("Tenant, workspace, and namespace are required.")


@dataclass(frozen=True, slots=True)
class KnowledgeBase:
    id: str
    name: str
    description: str
    owner: str
    scope: Scope
    status: KnowledgeStatus = KnowledgeStatus.DRAFT
    visibility: Visibility = Visibility.PRIVATE
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Collection:
    id: str
    knowledge_base_id: str
    name: str
    scope: Scope
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Document:
    id: str
    knowledge_base_id: str
    collection_id: str | None
    name: str
    scope: Scope
    version: int
    checksum: str
    source: str
    content_type: str
    size: int
    status: KnowledgeStatus = KnowledgeStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Chunk:
    id: str
    document_id: str
    text: str
    index: int
    token_count: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Citation:
    id: str
    document_id: str
    chunk_id: str
    page: int | None = None
    section: str | None = None
    source_url: str | None = None
    excerpt: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
