"""Security scanning provider interface."""

from typing import Protocol


class SecurityScanner(Protocol):
    def scan(self, reference: str) -> dict[str, object]: ...


__all__ = ("SecurityScanner",)
