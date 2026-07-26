"""Searchable in-memory enterprise plugin catalog."""

from __future__ import annotations

from threading import RLock

from tkai.core.exceptions import PluginError

from ..models import PluginDefinition


class PluginCatalog:
    def __init__(self) -> None:
        self._items: dict[str, dict[str, PluginDefinition]] = {}
        self._lock = RLock()

    def publish(self, definition: PluginDefinition) -> None:
        with self._lock:
            versions = self._items.setdefault(definition.plugin_id, {})
            versions[definition.version] = definition

    def get(self, plugin_id: str, version: str | None = None) -> PluginDefinition:
        with self._lock:
            versions = self._items.get(plugin_id)
            if not versions:
                raise PluginError(f"Plugin '{plugin_id}' is not in the catalog")
            selected = version or max(versions, key=_version_key)
            try:
                return versions[selected]
            except KeyError as exc:
                raise PluginError(
                    f"Plugin '{plugin_id}' version '{selected}' is not in the catalog"
                ) from exc

    def list(self) -> tuple[PluginDefinition, ...]:
        with self._lock:
            return tuple(
                self.get(plugin_id) for plugin_id in sorted(self._items)
            )

    def search(
        self, query: str = "", *, category: str = "", tag: str = ""
    ) -> tuple[PluginDefinition, ...]:
        needle = query.casefold()
        return tuple(
            item
            for item in self.list()
            if (
                not needle
                or needle in item.name.casefold()
                or needle in item.description.casefold()
                or needle in item.plugin_id.casefold()
            )
            and (not category or item.category == category)
            and (not tag or tag in item.tags)
        )

    def categories(self) -> tuple[str, ...]:
        return tuple(sorted({item.category for item in self.list()}))

    def tags(self) -> tuple[str, ...]:
        return tuple(sorted({tag for item in self.list() for tag in item.tags}))


def _version_key(value: str) -> tuple[tuple[int, object], ...]:
    return tuple(
        (0, int(part)) if part.isdigit() else (1, part)
        for part in value.replace("-", ".").split(".")
    )


__all__ = ("PluginCatalog",)
