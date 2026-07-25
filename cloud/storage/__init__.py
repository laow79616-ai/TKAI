"""Offline Cloud Storage Foundation contracts and reference-only service."""

from .context import StorageContext
from .factory import StorageFactory
from .lifecycle import StorageLifecycle, StorageStatus
from .models import StorageBucket, StorageDescriptor, StorageObject
from .reference import ReferenceStorageService
from .registry import StorageRegistry

__all__ = (
    "ReferenceStorageService",
    "StorageBucket",
    "StorageContext",
    "StorageDescriptor",
    "StorageFactory",
    "StorageLifecycle",
    "StorageObject",
    "StorageRegistry",
    "StorageStatus",
)
