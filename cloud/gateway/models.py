from dataclasses import dataclass
from enum import Enum


class GatewayHealth(str, Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass(frozen=True, slots=True)
class GatewayCapability:
    name: str
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class GatewayVersion:
    platform_version: str
    cloud_version: str = "4"
