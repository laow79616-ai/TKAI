"""Thread-safe metadata registries used by the Hyper Kernel."""

from __future__ import annotations

from collections.abc import Iterable
from threading import RLock

from tkai.v8.contracts import FrameworkKind, RegistryRecord, Scope


class RegistryError(RuntimeError):
    """Base registry error."""


class DuplicateRegistrationError(RegistryError):
    """Raised when an identifier is registered twice in the same scope."""


class MetadataRegistry:
    """Isolated registry that stores references and metadata, never executors."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._records: dict[tuple[str, str, str, str], RegistryRecord] = {}
        self._lock = RLock()

    @staticmethod
    def _key(record: RegistryRecord) -> tuple[str, str, str, str]:
        scope = record.scope
        return (scope.tenant, scope.workspace, scope.framework, record.identifier)

    def register(self, record: RegistryRecord) -> RegistryRecord:
        key = self._key(record)
        with self._lock:
            if key in self._records:
                raise DuplicateRegistrationError(record.identifier)
            self._records[key] = record
        return record

    def get(self, identifier: str, scope: Scope | None = None) -> RegistryRecord:
        selected_scope = scope or Scope()
        try:
            return self._records[
                (
                    selected_scope.tenant,
                    selected_scope.workspace,
                    selected_scope.framework,
                    identifier,
                )
            ]
        except KeyError as error:
            raise RegistryError(identifier) from error

    def discover(
        self,
        *,
        scope: Scope | None = None,
        kind: str | None = None,
        capability: str | None = None,
    ) -> tuple[RegistryRecord, ...]:
        records: Iterable[RegistryRecord] = self._records.values()
        if scope is not None:
            records = (
                record
                for record in records
                if record.scope.tenant == scope.tenant
                and record.scope.workspace == scope.workspace
                and (
                    scope.framework == "*" or record.scope.framework == scope.framework
                )
            )
        if kind is not None:
            records = (record for record in records if record.kind == kind)
        if capability is not None:
            records = (
                record for record in records if capability in record.capabilities
            )
        return tuple(
            sorted(records, key=lambda record: (record.kind, record.identifier))
        )

    def identifiers(self) -> tuple[str, ...]:
        return tuple(record.identifier for record in self.discover())

    def __len__(self) -> int:
        return len(self._records)


class FrameworkRegistry(MetadataRegistry):
    """Registry constrained to known or explicitly future framework families."""

    def __init__(self) -> None:
        super().__init__("frameworks")

    def register(self, record: RegistryRecord) -> RegistryRecord:
        supported = {kind.value for kind in FrameworkKind}
        if record.kind not in supported:
            raise RegistryError(
                f"unsupported framework kind {record.kind!r}; use 'future'"
            )
        return super().register(record)

    def supported_kinds(self) -> tuple[str, ...]:
        return tuple(kind.value for kind in FrameworkKind)


class RegistryCatalog:
    """Named collection of every Hyper Kernel registry."""

    NAMES = (
        "frameworks",
        "capabilities",
        "runtime",
        "modules",
        "extensions",
        "compatibility",
        "diagnostics",
    )

    def __init__(self) -> None:
        self.frameworks = FrameworkRegistry()
        self.capabilities = MetadataRegistry("capabilities")
        self.runtime = MetadataRegistry("runtime")
        self.modules = MetadataRegistry("modules")
        self.extensions = MetadataRegistry("extensions")
        self.compatibility = MetadataRegistry("compatibility")
        self.diagnostics = MetadataRegistry("diagnostics")

    def values(self) -> Iterable[MetadataRegistry]:
        return (
            self.frameworks,
            self.capabilities,
            self.runtime,
            self.modules,
            self.extensions,
            self.compatibility,
            self.diagnostics,
        )


__all__ = (
    "DuplicateRegistrationError",
    "FrameworkRegistry",
    "MetadataRegistry",
    "RegistryCatalog",
    "RegistryError",
)
