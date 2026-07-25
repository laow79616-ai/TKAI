from threading import RLock

from .errors import StorageConflictError, StorageNotFoundError


class StorageRegistry:
    def __init__(self):
        self._lock = RLock()
        self._stores = {}
        self._buckets = {}
        self._objects = {}

    def register(self, item):
        with self._lock:
            if item.storage_id in self._stores:
                raise StorageConflictError(item.storage_id)
            self._stores[item.storage_id] = item
            return item

    def get(self, key):
        with self._lock:
            try:
                return self._stores[key]
            except KeyError as exc:
                raise StorageNotFoundError(key) from exc

    def list(self):
        with self._lock:
            return tuple(v for _, v in sorted(self._stores.items()))

    def exists(self, key):
        with self._lock:
            return key in self._stores

    def unregister(self, key):
        with self._lock:
            item = self.get(key)
            del self._stores[key]
            return item

    def snapshot(self):
        return self.list()

    def add_bucket(self, item):
        with self._lock:
            self._buckets[item.bucket_id] = item
            return item

    def add_object(self, item):
        with self._lock:
            self._objects[item.object_id] = item
            return item

    def objects(self, bucket_id):
        with self._lock:
            return tuple(
                v for _, v in sorted(self._objects.items()) if v.bucket_id == bucket_id
            )

    def delete_object(self, key):
        with self._lock:
            try:
                return self._objects.pop(key)
            except KeyError as exc:
                raise StorageNotFoundError(key) from exc

    def clear(self):
        with self._lock:
            self._stores.clear()
            self._buckets.clear()
            self._objects.clear()
