"""Typed domain models for the enterprise TikTok browser runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BrowserStatus(str, Enum):
    DRAFT = "draft"
    PROVISIONING = "provisioning"
    READY = "ready"
    RUNNING = "running"
    IDLE = "idle"
    PAUSED = "paused"
    RECOVERING = "recovering"
    FAILED = "failed"
    STOPPED = "stopped"
    ARCHIVED = "archived"
    DELETED = "deleted"


class BrowserEngine(str, Enum):
    CHROMIUM = "chromium"
    CHROME = "chrome"
    EDGE = "edge"
    PLAYWRIGHT = "playwright"


class ContextMode(str, Enum):
    PERSISTENT = "persistent"
    EPHEMERAL = "ephemeral"


class ProxyProtocol(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS5 = "socks5"


@dataclass(frozen=True, slots=True)
class RuntimeScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:browser:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class FingerprintConfiguration:
    canvas_policy: str = "native"
    webgl_policy: str = "native"
    audio_context_policy: str = "native"
    fonts_reference: str = ""
    hardware_concurrency: int = 4
    device_memory: int = 8
    platform: str = "Win32"
    touch_support: bool = False
    media_devices_interface: str = "default"

    def validate(self) -> None:
        policies = {"native", "disabled", "managed"}
        if (
            self.canvas_policy not in policies
            or self.webgl_policy not in policies
            or self.audio_context_policy not in policies
        ):
            raise ValueError(
                "Fingerprint policies must be native, disabled, or managed."
            )
        if self.hardware_concurrency < 1 or self.device_memory < 1:
            raise ValueError("Fingerprint hardware values must be positive.")
        if self.touch_support and self.platform == "Win32":
            raise ValueError("Touch support is inconsistent with the Win32 profile.")


@dataclass(slots=True)
class BrowserProfile:
    id: str
    tenant: str
    workspace: str
    account_reference: str = ""
    profile_directory_reference: str = ""
    user_agent: str = ""
    timezone: str = "UTC"
    locale: str = "en-US"
    languages: tuple[str, ...] = ("en-US",)
    viewport: tuple[int, int] = (1280, 720)
    screen_resolution: tuple[int, int] = (1920, 1080)
    device_scale_factor: float = 1.0
    color_scheme: str = "light"
    geolocation_reference: str = ""
    permissions: tuple[str, ...] = ()
    download_directory_reference: str = ""
    fingerprint: FingerprintConfiguration = field(
        default_factory=FingerprintConfiguration
    )


@dataclass(slots=True)
class ProxyBinding:
    id: str
    tenant: str
    workspace: str
    protocol: ProxyProtocol
    host: str
    port: int
    username_reference: str = ""
    password_secret_reference: str = ""
    country: str = ""
    region: str = ""
    health: str = "unknown"
    sticky_session_reference: str = ""


@dataclass(slots=True)
class BrowserInstance:
    id: str
    name: str
    account_reference: str
    tenant: str
    workspace: str
    owner: str
    engine: BrowserEngine = BrowserEngine.CHROMIUM
    profile_reference: str = ""
    proxy_reference: str = ""
    status: BrowserStatus = BrowserStatus.DRAFT
    process_id_reference: str = ""
    headless: bool = True
    context_mode: ContextMode = ContextMode.EPHEMERAL
    created_at: datetime = field(default_factory=utcnow)
    last_active_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["engine"] = self.engine.value
        result["status"] = self.status.value
        result["context_mode"] = self.context_mode.value
        result["created_at"] = self.created_at.isoformat()
        result["last_active_at"] = self.last_active_at.isoformat()
        return result


@dataclass(slots=True)
class BrowserContext:
    id: str
    instance_id: str
    tenant: str
    workspace: str
    persistent: bool = False
    storage_reference: str = ""
    maximum_lifetime_seconds: int = 3600
    idle_timeout_seconds: int = 300
    status: str = "created"
    created_at: datetime = field(default_factory=utcnow)
    last_active_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class BrowserPage:
    id: str
    context_id: str
    tenant: str
    workspace: str
    url: str = "about:blank"
    title: str = ""
    health: str = "healthy"
    active: bool = True
    screenshot_reference: str = ""
    navigation_history: list[str] = field(default_factory=lambda: ["about:blank"])
    history_index: int = 0


@dataclass(slots=True)
class HealthSnapshot:
    instance_id: str
    process: str
    context: str
    page: str
    tiktok_reachability: str
    login: str
    proxy: str
    memory_bytes: int
    cpu_reference: str
    last_heartbeat: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class RecoveryRecord:
    instance_id: str
    attempts: int
    maximum_attempts: int
    backoff_seconds: float
    failure_reason: str
    recovered: bool = False


@dataclass(order=True, slots=True)
class LaunchRequest:
    sort_key: tuple[int, datetime]
    id: str = field(compare=False)
    instance_id: str = field(compare=False)
    tenant: str = field(compare=False)
    workspace: str = field(compare=False)
    account_reference: str = field(compare=False)
    priority: int = field(compare=False, default=0)
    timeout_seconds: int = field(compare=False, default=30)
    cancelled: bool = field(compare=False, default=False)
