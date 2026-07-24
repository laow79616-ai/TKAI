import pytest

from cloud.storage import (
    ReferenceStorageService,
    StorageContext,
    StorageLifecycle,
    StorageStatus,
)
from cloud.storage.errors import StorageLifecycleError
from cloud.storage.models import StorageDescriptor


def test_storage_reference_is_in_memory_and_deterministic():
    service = ReferenceStorageService()
    service.registry.register(StorageDescriptor("s", "p", "w", "store"))
    bucket = service.create_bucket("b", "s", "bucket")
    obj = service.create_object("o", bucket.bucket_id, "object", size=1)
    assert service.get("s").project_id == "p"
    assert service.delete(obj.object_id) == obj
    service.close()
    service.close()
    assert service.list() == ()


def test_context_lifecycle_and_no_invalid_transition():
    assert StorageContext(workspace_id="w").to_dict()["workspace_id"] == "w"
    assert (
        StorageLifecycle().transition(StorageStatus.CREATED, StorageStatus.AVAILABLE)
        is StorageStatus.AVAILABLE
    )
    with pytest.raises(StorageLifecycleError):
        StorageLifecycle().transition(StorageStatus.DELETED, StorageStatus.AVAILABLE)
