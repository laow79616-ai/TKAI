"""Deny-by-default capability permissions and isolation."""

from __future__ import annotations

from collections.abc import Iterable

from tkai.v7.security import AccessController, IsolationPolicy, Principal


class PermissionValidator:
    def __init__(self, grants: Iterable[str] = ()) -> None:
        self.grants = frozenset(grants)

    def validate(self, required: Iterable[str]) -> None:
        missing = frozenset(required) - self.grants
        if missing:
            raise PermissionError(
                f"permissions not granted: {', '.join(sorted(missing))}"
            )


__all__ = (
    "AccessController",
    "IsolationPolicy",
    "PermissionValidator",
    "Principal",
)
