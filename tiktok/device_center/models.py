"""Domain models for the enterprise local TikTok Device Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DeviceStatus(str, Enum):
    DISCOVERED = "discovered"
    PROVISIONING = "provisioning"
    READY = "ready"
    RUNNING = "running"
    BUSY = "busy"
    PAUSED = "paused"
    RECOVERING = "recovering"
    OFFLINE = "offline"
    ARCHIVED = "archived"
    DELETED = "deleted"


class DeviceType(str, Enum):
    ANDROID = "android"
    IPHONE = "iphone"
    ANDROID_EMULATOR = "android_emulator"
    IOS_SIMULATOR_REFERENCE = "ios_simulator_reference"
    VIRTUAL_DEVICE = "virtual_device"
    FUTURE_EXTENSION = "future_extension"


@dataclass(frozen=True, slots=True)
class DeviceScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:device-center:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class Device:
    id: str
    name: str
    type: DeviceType
    platform: str
    model: str
    serial_reference: str
    tenant: str
    workspace: str
    owner: str
    status: DeviceStatus = DeviceStatus.DISCOVERED
    metadata: dict[str, Any] = field(default_factory=dict)
    profile_id: str = ""
    group_ids: set[str] = field(default_factory=set)
    account_reference: str = ""
    reserved_by: str = ""
    reserved_until: datetime | None = None
    cooldown_until: datetime | None = None
    discovered_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class DeviceGroup:
    id: str
    name: str
    tenant: str
    workspace: str
    owner: str
    device_ids: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DeviceProfile:
    id: str
    name: str
    tenant: str
    workspace: str
    resolution: str
    language: str
    timezone: str
    locale: str
    region: str
    device_profile: str
    version: int = 1

    def validate(self) -> None:
        required = (
            self.id,
            self.name,
            self.resolution,
            self.language,
            self.timezone,
            self.locale,
            self.region,
            self.device_profile,
        )
        if not all(required) or self.version < 1:
            raise ValueError(
                "Complete profile fields and a positive version are required."
            )
        if "x" not in self.resolution.casefold():
            raise ValueError("Resolution must use WIDTHxHEIGHT format.")


@dataclass(slots=True)
class AllocationPolicy:
    maximum_concurrent_devices: int = 20
    workspace_limit: int = 10
    account_limit: int = 1
    reservation_timeout_seconds: float = 300.0
    cooldown_seconds: float = 30.0

    def validate(self) -> None:
        if (
            min(
                self.maximum_concurrent_devices,
                self.workspace_limit,
                self.account_limit,
            )
            < 1
            or min(self.reservation_timeout_seconds, self.cooldown_seconds) < 0
        ):
            raise ValueError("Resource allocation limits are invalid.")
        if self.workspace_limit > self.maximum_concurrent_devices:
            raise ValueError("Workspace limit cannot exceed the global limit.")


@dataclass(order=True, slots=True)
class DeviceQueueItem:
    sort_key: tuple[int, datetime, int]
    id: str = field(compare=False)
    tenant: str = field(compare=False)
    workspace: str = field(compare=False)
    requester: str = field(compare=False)
    account_reference: str = field(compare=False)
    device_type: DeviceType | None = field(compare=False, default=None)
    priority: int = field(compare=False, default=0)
    attempts: int = field(compare=False, default=0)
    available_at: datetime = field(compare=False, default_factory=utcnow)


@dataclass(slots=True)
class Reservation:
    id: str
    device_id: str
    tenant: str
    workspace: str
    requester: str
    account_reference: str
    created_at: datetime
    expires_at: datetime
    released_at: datetime | None = None


@dataclass(slots=True)
class HealthSnapshot:
    device_id: str
    connectivity: bool
    battery: float
    cpu: float
    memory: float
    storage: float
    runtime_seconds: float
    temperature_reference: str = ""
    heartbeat: datetime = field(default_factory=utcnow)
    score: float = 100.0
    failed: bool = False

    def validate(self) -> None:
        percentages = (self.battery, self.cpu, self.memory, self.storage)
        if any(value < 0 or value > 100 for value in percentages):
            raise ValueError("Health percentages must be between 0 and 100.")
        if self.runtime_seconds < 0:
            raise ValueError("Runtime cannot be negative.")


@dataclass(slots=True)
class RecoveryPolicy:
    maximum_attempts: int = 3
    cooldown_seconds: float = 30.0
    manual_approval: bool = False

    def validate(self) -> None:
        if self.maximum_attempts < 1 or self.cooldown_seconds < 0:
            raise ValueError("Recovery policy values are invalid.")


@dataclass(slots=True)
class RecoveryRecord:
    device_id: str
    attempt: int
    reason: str
    actions: tuple[str, ...]
    recovered: bool
    stopped_for_restriction: bool = False
    manual_approval_required: bool = False
    occurred_at: datetime = field(default_factory=utcnow)


def serialize(value: Any) -> dict[str, Any]:
    result = asdict(value)
    for key, item in tuple(result.items()):
        if isinstance(item, Enum):
            result[key] = item.value
        elif isinstance(item, datetime):
            result[key] = item.isoformat()
        elif isinstance(item, set):
            result[key] = sorted(item)
    return result
