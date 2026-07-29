"""Interface catalog and version negotiation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tkai.v7.contracts import Version, VersionRange


class InterfaceNotFoundError(LookupError):
    """Raised when no compatible interface contract is registered."""


@dataclass(frozen=True)
class InterfaceContract:
    """A named interface implementation at a specific version."""

    name: str
    version: Version
    interface: type[Any]


class InterfaceRegistry:
    """Registers and negotiates stable interface contracts."""

    def __init__(self) -> None:
        self._contracts: dict[str, dict[Version, InterfaceContract]] = {}

    def register(self, contract: InterfaceContract) -> None:
        versions = self._contracts.setdefault(contract.name, {})
        if contract.version in versions:
            raise ValueError(
                f"interface {contract.name!r} version {contract.version} exists"
            )
        versions[contract.version] = contract

    def negotiate(
        self, name: str, supported: VersionRange | None = None
    ) -> InterfaceContract:
        versions = self._contracts.get(name, {})
        candidates = [
            contract
            for version, contract in versions.items()
            if supported is None or supported.supports(version)
        ]
        if not candidates:
            raise InterfaceNotFoundError(name)
        return max(candidates, key=lambda contract: contract.version)

    def list(self) -> tuple[InterfaceContract, ...]:
        return tuple(
            sorted(
                (
                    item
                    for versions in self._contracts.values()
                    for item in versions.values()
                ),
                key=lambda item: (item.name, item.version),
            )
        )


__all__ = ("InterfaceContract", "InterfaceNotFoundError", "InterfaceRegistry")
