"""Stable Enterprise errors without sensitive detail."""


class EnterpriseError(Exception):
    pass


class EnterpriseConflictError(EnterpriseError):
    pass


class EnterpriseNotFoundError(EnterpriseError):
    pass


class EnterprisePermissionError(EnterpriseError):
    pass


class EnterpriseClosedError(EnterpriseError):
    pass


class EnterpriseAuthenticationError(EnterpriseError):
    pass
