"""Immutable namespace identifiers for isolated local memory collections."""

from dataclasses import dataclass

from .errors import MemoryConfigurationError


@dataclass(frozen=True, slots=True)
class MemoryNamespace:
    """A validated application-controlled namespace name."""

    name: str = "default"

    def __post_init__(self) -> None:
        if not self.name:
            raise MemoryConfigurationError("Memory namespace must not be empty.")
