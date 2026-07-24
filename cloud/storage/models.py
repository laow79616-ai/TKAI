from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..models import CloudValue, snapshot


@dataclass(frozen=True, slots=True)
class StorageDescriptor:
    storage_id: str
    project_id: str
    workspace_id: str
    name: str
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not all((self.storage_id, self.project_id, self.workspace_id, self.name)):
            raise ValueError("Storage identifiers and name are required.")
        object.__setattr__(self, "metadata", snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class StorageBucket:
    bucket_id: str
    storage_id: str
    name: str
    tags: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not all((self.bucket_id, self.storage_id, self.name)):
            raise ValueError("Bucket identifiers and name are required.")
        object.__setattr__(self, "tags", frozenset(self.tags))
        object.__setattr__(self, "metadata", snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class StorageObject:
    object_id: str
    bucket_id: str
    name: str
    content_type: str = "application/octet-stream"
    size: int = 0
    checksum: str | None = None
    tags: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not all((self.object_id, self.bucket_id, self.name)) or self.size < 0:
            raise ValueError(
                "Object ids/name are required and size must not be negative."
            )
        object.__setattr__(self, "tags", frozenset(self.tags))
        object.__setattr__(self, "metadata", snapshot(self.metadata))
