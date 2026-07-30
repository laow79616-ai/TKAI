"""Bounded, isolated registries containing metadata references only."""

from __future__ import annotations

from collections.abc import Iterable

from tkai.v9.contracts import Reference, Scope


class RegistryError(ValueError):
    pass


class BoundedRegistry:
    def __init__(self, name: str, *, limit: int = 1_000) -> None:
        if limit < 1:
            raise ValueError("limit must be positive")
        self.name, self.limit = name, limit
        self._records: dict[tuple[str, str, str, str], Reference] = {}

    @staticmethod
    def _key(record: Reference) -> tuple[str, str, str, str]:
        scope = record.scope
        return scope.tenant, scope.workspace, scope.namespace, record.identifier

    def register(self, record: Reference) -> Reference:
        key = self._key(record)
        if key in self._records:
            raise RegistryError(f"duplicate reference: {record.identifier}")
        if len(self._records) >= self.limit:
            raise RegistryError(f"{self.name} registry limit exceeded")
        self._records[key] = record
        return record

    def discover(
        self, *, scope: Scope | None = None, kind: str | None = None, limit: int = 100
    ) -> tuple[Reference, ...]:
        if limit < 0 or limit > 500:
            raise RegistryError("result limit must be between 0 and 500")
        records: Iterable[Reference] = self._records.values()
        if scope:
            records = (
                record
                for record in records
                if record.scope.tenant == scope.tenant
                and record.scope.workspace == scope.workspace
                and record.scope.namespace == scope.namespace
            )
        if kind:
            records = (record for record in records if record.kind == kind)
        return tuple(sorted(records, key=lambda item: item.identifier))[:limit]

    def get(self, identifier: str, scope: Scope | None = None) -> Reference:
        selected_scope = scope or Scope()
        try:
            return self._records[
                (
                    selected_scope.tenant,
                    selected_scope.workspace,
                    selected_scope.namespace,
                    identifier,
                )
            ]
        except KeyError as error:
            raise RegistryError(f"unknown reference: {identifier}") from error

    def __len__(self) -> int:
        return len(self._records)


class RegistryCatalog:
    NAMES = (
        "frameworks",
        "capabilities",
        "services",
        "modules",
        "extensions",
        "runtime",
        "policies",
        "constraints",
        "compatibility",
        "adaptations",
        "change_plans",
        "diagnostics",
        "health",
        "contexts",
    )

    def __init__(self, *, per_registry_limit: int = 1_000) -> None:
        self.frameworks: BoundedRegistry
        self.capabilities: BoundedRegistry
        self.services: BoundedRegistry
        self.modules: BoundedRegistry
        self.extensions: BoundedRegistry
        self.runtime: BoundedRegistry
        self.policies: BoundedRegistry
        self.constraints: BoundedRegistry
        self.compatibility: BoundedRegistry
        self.adaptations: BoundedRegistry
        self.change_plans: BoundedRegistry
        self.diagnostics: BoundedRegistry
        self.health: BoundedRegistry
        self.contexts: BoundedRegistry
        for name in self.NAMES:
            setattr(self, name, BoundedRegistry(name, limit=per_registry_limit))

    def values(self) -> tuple[BoundedRegistry, ...]:
        return tuple(getattr(self, name) for name in self.NAMES)

    def get(self, name: str) -> BoundedRegistry:
        if name not in self.NAMES:
            raise RegistryError(f"unknown registry: {name}")
        registry = getattr(self, name)
        assert isinstance(registry, BoundedRegistry)
        return registry


__all__ = ("BoundedRegistry", "RegistryCatalog", "RegistryError")
