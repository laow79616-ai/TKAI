class DeploymentError(Exception):
    pass


class DeploymentNotFoundError(DeploymentError):
    pass


class DeploymentConflictError(DeploymentError):
    pass


class DeploymentValidationError(DeploymentError):
    pass


class DeploymentTargetError(DeploymentError):
    pass


class DeploymentPlanError(DeploymentError):
    pass


class DeploymentLifecycleError(DeploymentError):
    pass


class DeploymentClosedError(DeploymentError):
    pass
