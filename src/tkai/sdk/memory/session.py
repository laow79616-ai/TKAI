"""Immutable session identifiers for local conversation memory isolation."""

from dataclasses import dataclass

from .errors import MemoryConfigurationError


@dataclass(frozen=True, slots=True)
class MemorySession:
    """A validated caller-supplied session identifier."""

    identifier: str

    def __post_init__(self) -> None:
        if not self.identifier:
            raise MemoryConfigurationError(
                "Memory session identifier must not be empty."
            )
