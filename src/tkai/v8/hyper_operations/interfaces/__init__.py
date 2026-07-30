"""Read-only provider interface for operations metadata."""

from collections.abc import Mapping, Sequence
from typing import Protocol


class OperationsMetadataProvider(Protocol):
    @property
    def read_only(self) -> bool: ...
    def read(
        self, records: Sequence[Mapping[str, object]]
    ) -> tuple[Mapping[str, object], ...]: ...


__all__ = ("OperationsMetadataProvider",)
