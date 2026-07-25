"""Credential discovery failures that never embed secret values."""


class CredentialError(RuntimeError):
    """Base credential subsystem error."""


class CredentialNotFoundError(CredentialError):
    """No configured credential source could resolve the provider."""


class CredentialSourceError(CredentialError):
    """A local credential source is malformed or unavailable."""
