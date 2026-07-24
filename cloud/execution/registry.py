from threading import RLock

from .errors import ExecutionConflictError, ExecutionNotFoundError


class ExecutionRegistry:
    def __init__(self):
        self._lock = RLock()
        self._items = {}

    def register(self, item):
        with self._lock:
            if item.execution_id in self._items:
                raise ExecutionConflictError(item.execution_id)
            self._items[item.execution_id] = item
            return item

    def get(self, key):
        with self._lock:
            try:
                return self._items[key]
            except KeyError as exc:
                raise ExecutionNotFoundError(key) from exc

    def list(self):
        with self._lock:
            return tuple(v for _, v in sorted(self._items.items()))

    def snapshot(self):
        return self.list()

    def clear(self):
        with self._lock:
            self._items.clear()
