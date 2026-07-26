"""Enterprise plugin permission declarations and enforcement."""

from dataclasses import dataclass
from enum import Enum

from tkai.core.exceptions import PluginError


class PluginPermission(str, Enum):
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    ENVIRONMENT = "environment"
    SECRETS = "secrets"
    API = "api"
    DATABASE = "database"
    WORKFLOW = "workflow"
    AGENT = "agent"


@dataclass(frozen=True, slots=True)
class PermissionPolicy:
    allowed: frozenset[PluginPermission] = frozenset()

    def validate(self, requested: frozenset[str]) -> None:
        known = {permission.value for permission in PluginPermission}
        unknown = requested - known
        denied = requested - {permission.value for permission in self.allowed}
        if unknown:
            raise PluginError(f"Unknown plugin permissions: {sorted(unknown)}")
        if denied:
            raise PluginError(f"Denied plugin permissions: {sorted(denied)}")

    def permits(self, permission: PluginPermission) -> bool:
        return permission in self.allowed


__all__ = ("PermissionPolicy", "PluginPermission")
