"""Plugin package installation facade."""

from dataclasses import dataclass

from ..marketplace import EnterprisePluginMarketplace
from ..models import InstalledPlugin


@dataclass(slots=True)
class PluginInstaller:
    marketplace: EnterprisePluginMarketplace

    def install(self, plugin_id: str, version: str | None = None) -> InstalledPlugin:
        return self.marketplace.install(plugin_id, version)

    def uninstall(self, plugin_id: str) -> InstalledPlugin:
        return self.marketplace.uninstall(plugin_id)

    def upgrade(self, plugin_id: str, version: str | None = None) -> InstalledPlugin:
        return self.marketplace.upgrade(plugin_id, version)

    def rollback(self, plugin_id: str) -> InstalledPlugin:
        return self.marketplace.rollback(plugin_id)


__all__ = ("PluginInstaller",)
