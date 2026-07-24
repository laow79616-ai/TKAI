"""Stable errors for the offline Marketplace Registry Foundation."""


class RegistryError(Exception):
    """Base error for Registry Foundation models and local service operations."""


class RegistryValidationError(RegistryError):
    """Raised when a local registry entry lacks required structure."""


class RegistryConflictError(RegistryError):
    """Raised for duplicate entry identifiers or publication coordinates."""


class RegistryNotFoundError(RegistryError):
    """Raised when an explicit local entry or coordinate cannot be found."""


class RegistryStateError(RegistryError):
    """Raised for invalid descriptive registry-state operations."""


class RegistryClosedError(RegistryError):
    """Raised when an operation is attempted after local service close."""


class RegistryPublicationError(RegistryError):
    """Raised when a publication cannot explicitly become a registry entry."""
