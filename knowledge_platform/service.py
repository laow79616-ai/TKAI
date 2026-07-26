"""Enterprise knowledge facade and lifecycle."""

from dataclasses import replace

from .core import CollectionStore, DocumentStore, KnowledgeBaseStore
from .metrics import KnowledgeMetrics
from .models import KnowledgeBase, KnowledgeStatus, Scope
from .permissions import PermissionService
from .security import SecurityPolicy

TRANSITIONS = {
    KnowledgeStatus.DRAFT: {KnowledgeStatus.INDEXING, KnowledgeStatus.DELETED},
    KnowledgeStatus.INDEXING: {KnowledgeStatus.READY, KnowledgeStatus.FAILED},
    KnowledgeStatus.READY: {
        KnowledgeStatus.PAUSED,
        KnowledgeStatus.INDEXING,
        KnowledgeStatus.ARCHIVED,
    },
    KnowledgeStatus.PAUSED: {KnowledgeStatus.INDEXING, KnowledgeStatus.ARCHIVED},
    KnowledgeStatus.FAILED: {KnowledgeStatus.INDEXING, KnowledgeStatus.ARCHIVED},
    KnowledgeStatus.ARCHIVED: {KnowledgeStatus.DRAFT, KnowledgeStatus.DELETED},
    KnowledgeStatus.DELETED: set(),
}


class KnowledgePlatform:
    def __init__(self, policy: SecurityPolicy | None = None) -> None:
        self.policy = policy or SecurityPolicy()
        self.bases = KnowledgeBaseStore()
        self.collections = CollectionStore()
        self.documents = DocumentStore(self.policy)
        self.permissions = PermissionService()
        self.metrics = KnowledgeMetrics()

    def create_base(self, payload: dict[str, object]) -> KnowledgeBase:
        item = self.bases.create(payload)
        self.metrics.increment("knowledge_bases_total")
        return item

    def transition(self, item_id: str, scope: Scope, status: str) -> KnowledgeBase:
        item = self.bases.get(item_id, scope)
        target = KnowledgeStatus(status)
        if target not in TRANSITIONS[item.status]:
            raise ValueError(
                f"Invalid transition: {item.status.value} -> {target.value}"
            )
        return self.bases.replace(replace(item, status=target))
