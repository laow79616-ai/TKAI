from typing import Protocol


class ExecutionService(Protocol):
    def list(self) -> tuple[object, ...]: ...
