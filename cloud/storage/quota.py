from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StorageQuota:
    capacity_bytes: int | None = None
    object_limit: int | None = None
    version_limit: int | None = None


@dataclass(frozen=True, slots=True)
class StorageUsage:
    bytes_used: int = 0
    object_count: int = 0
    version_count: int = 0


@dataclass(frozen=True, slots=True)
class StorageDecision:
    valid: bool
    warnings: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
