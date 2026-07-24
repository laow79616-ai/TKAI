"""Pure status transitions for descriptive in-memory installation sessions."""

from .errors import InstallerStateError
from .models import InstallationStatus


class InstallationLifecycle:
    _allowed = {
        InstallationStatus.PENDING: (InstallationStatus.PLANNED,),
        InstallationStatus.PLANNED: (
            InstallationStatus.RUNNING,
            InstallationStatus.CANCELLED,
        ),
        InstallationStatus.RUNNING: (
            InstallationStatus.SUCCEEDED,
            InstallationStatus.FAILED,
            InstallationStatus.CANCELLED,
        ),
    }

    def allowed_transitions(
        self, status: InstallationStatus
    ) -> tuple[InstallationStatus, ...]:
        return self._allowed.get(status, ())

    def can_transition(
        self, current: InstallationStatus, target: InstallationStatus
    ) -> bool:
        return target in self.allowed_transitions(current)

    def transition(
        self, current: InstallationStatus, target: InstallationStatus
    ) -> InstallationStatus:
        if not self.can_transition(current, target):
            raise InstallerStateError(
                f"Invalid installation transition: {current.value} -> {target.value}."
            )
        return target
