from enum import Enum

from .errors import ExecutionLifecycleError


class ExecutionStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class ExecutionLifecycle:
    _allowed = {
        ExecutionStatus.QUEUED: {ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED},
        ExecutionStatus.RUNNING: {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
        },
        ExecutionStatus.COMPLETED: {ExecutionStatus.ARCHIVED},
        ExecutionStatus.FAILED: {ExecutionStatus.ARCHIVED},
        ExecutionStatus.CANCELLED: {ExecutionStatus.ARCHIVED},
    }

    def transition(self, current, target):
        if target not in self._allowed.get(current, set()):
            raise ExecutionLifecycleError(
                f"Illegal execution transition: {current.value} -> {target.value}"
            )
        return target
