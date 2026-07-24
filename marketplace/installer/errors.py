"""Stable errors for the reference-only Installer Core Foundation."""


class InstallerError(Exception):
    pass


class InstallerValidationError(InstallerError):
    pass


class InstallerConflictError(InstallerError):
    pass


class InstallerNotFoundError(InstallerError):
    pass


class InstallerStateError(InstallerError):
    pass


class InstallerClosedError(InstallerError):
    pass
