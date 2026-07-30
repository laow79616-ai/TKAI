"""Bounded read-only interfaces for V6, V7 and V8 metadata sources."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol


class RecoveryMetadataSource(Protocol):
    @property
    def read_only(self) -> bool: ...

    def read(
        self, records: Sequence[Mapping[str, object]]
    ) -> tuple[Mapping[str, object], ...]: ...
