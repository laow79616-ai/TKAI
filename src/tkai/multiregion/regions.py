"""Region roles used by the deterministic local topology."""

from enum import Enum


class RegionRole(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    BACKUP = "backup"
    DISABLED = "disabled"
