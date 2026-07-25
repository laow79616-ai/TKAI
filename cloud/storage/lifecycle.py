from enum import Enum

from .errors import StorageLifecycleError


class StorageStatus(str, Enum):
    CREATED = "created"
    AVAILABLE = "available"
    ARCHIVED = "archived"
    DELETED = "deleted"


class StorageLifecycle:
    _allowed = {
        StorageStatus.CREATED: {StorageStatus.AVAILABLE, StorageStatus.DELETED},
        StorageStatus.AVAILABLE: {StorageStatus.ARCHIVED, StorageStatus.DELETED},
        StorageStatus.ARCHIVED: {StorageStatus.DELETED},
    }

    def transition(
        self, current: StorageStatus, target: StorageStatus
    ) -> StorageStatus:
        if target not in self._allowed.get(current, set()):
            raise StorageLifecycleError(
                f"Illegal storage transition: {current.value} -> {target.value}"
            )
        return target
