"""Explicit ResolutionResult boundary for Installer Core Foundation."""

from typing import Protocol

from ..resolver import DependencyCoordinate, ResolutionResult, ResolutionStatus
from .errors import InstallerValidationError


class ResolutionInstallationSource(Protocol):
    def coordinates(self) -> tuple[DependencyCoordinate, ...]: ...
    def dependency_order(self) -> tuple[DependencyCoordinate, ...]: ...


class ReferenceResolutionInstallationSource:
    def __init__(self, result: ResolutionResult) -> None:
        if result.status is not ResolutionStatus.RESOLVED:
            raise InstallerValidationError(
                "Installation requires a resolved ResolutionResult."
            )
        self._coordinates = tuple(result.selected_coordinates)
        self._order = tuple(result.dependency_order)

    def coordinates(self) -> tuple[DependencyCoordinate, ...]:
        return self._coordinates

    def dependency_order(self) -> tuple[DependencyCoordinate, ...]:
        return self._order
