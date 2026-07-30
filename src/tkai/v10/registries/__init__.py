"""Bounded, scope-isolated metadata registries."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from tkai.v10.contracts import Scope


class RegistryError(ValueError):
    pass


class BoundedRegistry:
    def __init__(self, name: str, *, limit: int = 1_000) -> None:
        if limit < 1:
            raise ValueError("limit must be positive")
        self.name, self.limit = name, limit
        self._records: dict[tuple[str, str, str, str], object] = {}

    @staticmethod
    def _identifier(record: object) -> str:
        for name in ("identifier", f"{type(record).__name__.lower()}_id", "context_id"):
            value = getattr(record, name, None)
            if isinstance(value, str):
                return value
        for name in (
            "trust_domain_id",
            "principal_id",
            "integrity_id",
            "attestation_id",
            "boundary_id",
            "change_plan_id",
        ):
            value = getattr(record, name, None)
            if isinstance(value, str):
                return value
        raise RegistryError("record has no supported identifier")

    @classmethod
    def _key(cls, record: object) -> tuple[str, str, str, str]:
        scope = getattr(record, "scope", Scope())
        return scope.tenant, scope.workspace, scope.namespace, cls._identifier(record)

    def register(self, record: object) -> object:
        key = self._key(record)
        if key in self._records:
            raise RegistryError(f"duplicate reference: {key[-1]}")
        if len(self._records) >= self.limit:
            raise RegistryError(f"{self.name} registry limit exceeded")
        self._records[key] = record
        return record

    def discover(
        self, *, scope: Scope | None = None, limit: int = 100
    ) -> tuple[object, ...]:
        if limit < 0 or limit > 500:
            raise RegistryError("result limit must be between 0 and 500")
        records: Iterable[tuple[tuple[str, str, str, str], object]] = (
            self._records.items()
        )
        if scope:
            records = (
                item
                for item in records
                if item[0][:3] == (scope.tenant, scope.workspace, scope.namespace)
            )
        return tuple(value for _, value in sorted(records, key=lambda item: item[0]))[
            :limit
        ]

    def __len__(self) -> int:
        return len(self._records)


class RegistryCatalog:
    NAMES = (
        "trust_domains",
        "identities",
        "principals",
        "policies",
        "constraints",
        "boundaries",
        "integrity",
        "attestations",
        "frameworks",
        "capabilities",
        "services",
        "modules",
        "extensions",
        "runtime",
        "compatibility",
        "change_plans",
        "diagnostics",
        "health",
    )

    def __init__(self, *, per_registry_limit: int = 1_000) -> None:
        self._registries = {
            name: BoundedRegistry(name, limit=per_registry_limit) for name in self.NAMES
        }

    def get(self, name: str) -> BoundedRegistry:
        try:
            return self._registries[name]
        except KeyError as error:
            raise RegistryError(f"unknown registry: {name}") from error

    def __getattr__(self, name: str) -> Any:
        if name in self._registries:
            return self._registries[name]
        raise AttributeError(name)


__all__ = ("BoundedRegistry", "RegistryCatalog", "RegistryError")
