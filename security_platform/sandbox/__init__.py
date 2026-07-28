"""Isolated security sandbox interface."""

from typing import Protocol


class SecuritySandbox(Protocol):
    def execute(
        self, workload: str, limits: dict[str, object]
    ) -> dict[str, object]: ...


__all__ = ("SecuritySandbox",)
