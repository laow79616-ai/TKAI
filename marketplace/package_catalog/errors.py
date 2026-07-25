"""Errors for the local, reference-only Package Catalog Foundation."""


class PackageCatalogError(Exception):
    """Base error for package manifest and catalog operations."""


class CatalogPackageConflictError(PackageCatalogError):
    """Raised when an explicit package id is already in a reference catalog."""


class CatalogPackageNotFoundError(PackageCatalogError):
    """Raised when an explicit package id is absent from a reference catalog."""
