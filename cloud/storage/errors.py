class StorageError(Exception):
    pass


class StorageNotFoundError(StorageError):
    pass


class StorageConflictError(StorageError):
    pass


class StorageLifecycleError(StorageError):
    pass
