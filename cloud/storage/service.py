from typing import Protocol


class StorageService(Protocol):
    def list(self) -> tuple[object, ...]: ...
