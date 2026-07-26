"""Security firewall policy interface."""

from typing import Protocol


class SecurityFirewall(Protocol):
    def allow(
        self, source: str, destination: str, context: dict[str, object]
    ) -> bool: ...


__all__ = ("SecurityFirewall",)
