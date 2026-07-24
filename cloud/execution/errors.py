class ExecutionError(Exception):
    pass


class ExecutionNotFoundError(ExecutionError):
    pass


class ExecutionConflictError(ExecutionError):
    pass


class ExecutionLifecycleError(ExecutionError):
    pass


class ExecutionClosedError(ExecutionError):
    pass
