from .factory import StorageFactory
from .registry import StorageRegistry


class ReferenceStorageService:
    def __init__(self, registry=None, factory=None):
        self.registry = registry or StorageRegistry()
        self.factory = factory or StorageFactory()
        self._closed = False

    def create_bucket(self, bucket_id, storage_id, name):
        return self.registry.add_bucket(
            self.factory.bucket(bucket_id, storage_id, name)
        )

    def create_object(self, object_id, bucket_id, name, **kwargs):
        return self.registry.add_object(
            self.factory.object(object_id, bucket_id, name, **kwargs)
        )

    def get(self, storage_id):
        return self.registry.get(storage_id)

    def list(self):
        return self.registry.list()

    def delete(self, object_id):
        return self.registry.delete_object(object_id)

    def snapshot(self):
        return self.registry.snapshot()

    def close(self):
        self.registry.clear()
        self._closed = True
