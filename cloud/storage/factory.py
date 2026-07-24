from .models import StorageBucket, StorageDescriptor, StorageObject


class StorageFactory:
    def storage(self, storage_id, project_id, workspace_id, name, metadata=None):
        return StorageDescriptor(
            storage_id,
            project_id,
            workspace_id,
            name,
            {} if metadata is None else metadata,
        )

    def bucket(self, bucket_id, storage_id, name):
        return StorageBucket(bucket_id, storage_id, name)

    def object(self, object_id, bucket_id, name, **kwargs):
        return StorageObject(object_id, bucket_id, name, **kwargs)
