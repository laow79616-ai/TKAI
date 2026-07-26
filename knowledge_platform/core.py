"""Bounded in-memory knowledge repositories."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from typing import Any

from .models import (
    Collection,
    Document,
    KnowledgeBase,
    KnowledgeStatus,
    Scope,
    Visibility,
)
from .security import SecurityPolicy, enforce_scope


class KnowledgeBaseStore:
    def __init__(self) -> None:
        self.items: dict[str, KnowledgeBase] = {}

    def create(self, payload: dict[str, Any]) -> KnowledgeBase:
        scope = Scope(
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload["namespace"]),
        )
        item = KnowledgeBase(
            str(payload["id"]),
            str(payload["name"]),
            str(payload.get("description", "")),
            str(payload["owner"]),
            scope,
            visibility=Visibility(str(payload.get("visibility", "private"))),
            metadata=dict(payload.get("metadata", {})),
        )
        if item.id in self.items:
            raise ValueError("Knowledge base already exists.")
        self.items[item.id] = item
        return item

    def get(self, item_id: str, scope: Scope) -> KnowledgeBase:
        item = self.items[item_id]
        enforce_scope(scope, item.scope)
        return item

    def list(self, scope: Scope) -> tuple[KnowledgeBase, ...]:
        return tuple(item for item in self.items.values() if item.scope == scope)

    def replace(self, item: KnowledgeBase) -> KnowledgeBase:
        self.items[item.id] = item
        return item


class CollectionStore:
    def __init__(self) -> None:
        self.items: dict[str, Collection] = {}

    def create(self, payload: dict[str, Any], scope: Scope) -> Collection:
        item = Collection(
            str(payload["id"]),
            str(payload["knowledge_base_id"]),
            str(payload["name"]),
            scope,
            dict(payload.get("metadata", {})),
        )
        if item.id in self.items:
            raise ValueError("Collection already exists.")
        self.items[item.id] = item
        return item

    def list(self, scope: Scope) -> tuple[Collection, ...]:
        return tuple(item for item in self.items.values() if item.scope == scope)


class DocumentStore:
    def __init__(self, policy: SecurityPolicy | None = None) -> None:
        self.policy = policy or SecurityPolicy()
        self.items: dict[str, Document] = {}
        self.history: dict[str, list[Document]] = {}

    def upload(self, payload: dict[str, Any], content: bytes, scope: Scope) -> Document:
        self.policy.validate_file(str(payload["content_type"]), len(content))
        if (
            sum(item.scope == scope for item in self.items.values())
            >= self.policy.max_documents
        ):
            raise ValueError("Document count limit exceeded.")
        item = Document(
            str(payload["id"]),
            str(payload["knowledge_base_id"]),
            str(payload["collection_id"]) if payload.get("collection_id") else None,
            str(payload["name"]),
            scope,
            1,
            hashlib.sha256(content).hexdigest(),
            str(payload.get("source", "upload")),
            str(payload["content_type"]),
            len(content),
            metadata=self.policy.redact(dict(payload.get("metadata", {}))),
        )
        if item.id in self.items:
            raise ValueError("Document already exists.")
        self.items[item.id] = item
        self.history[item.id] = [item]
        return item

    def get(self, item_id: str, scope: Scope) -> Document:
        item = self.items[item_id]
        enforce_scope(scope, item.scope)
        return item

    def update(self, item_id: str, content: bytes, scope: Scope) -> Document:
        old = self.get(item_id, scope)
        self.policy.validate_file(old.content_type, len(content))
        item = replace(
            old,
            version=old.version + 1,
            checksum=hashlib.sha256(content).hexdigest(),
            size=len(content),
        )
        self.items[item_id] = item
        self.history[item_id].append(item)
        return item

    def delete(self, item_id: str, scope: Scope) -> Document:
        item = replace(self.get(item_id, scope), status=KnowledgeStatus.DELETED)
        self.items[item_id] = item
        return item

    def versions(self, item_id: str, scope: Scope) -> tuple[Document, ...]:
        self.get(item_id, scope)
        return tuple(self.history[item_id])

    def list(self, scope: Scope) -> tuple[Document, ...]:
        return tuple(item for item in self.items.values() if item.scope == scope)
