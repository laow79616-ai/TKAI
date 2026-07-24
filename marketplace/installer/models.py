"""Immutable installer descriptors; none describe a filesystem operation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from ..resolver import DependencyCoordinate, ResolutionResult, ResolutionStatus


def _map(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


class InstallationStatus(str, Enum):
    PENDING = "pending"
    PLANNED = "planned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class InstallationStepType(str, Enum):
    VALIDATE = "validate"
    PREPARE = "prepare"
    INSTALL = "install"
    VERIFY = "verify"
    FINALIZE = "finalize"
    ROLLBACK = "rollback"


class InstallationStrategy(str, Enum):
    FRESH = "fresh"
    REINSTALL = "reinstall"
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"
    DRY_RUN = "dry_run"


class InstallationDecision(str, Enum):
    PROCEED = "proceed"
    REJECT = "reject"
    CANCEL = "cancel"
    ROLLBACK = "rollback"


class InstallationIssueCode(str, Enum):
    INVALID_RESOLUTION = "invalid_resolution"
    INVALID_REQUEST = "invalid_request"
    PACKAGE_ALREADY_INSTALLED = "package_already_installed"
    VERSION_CONFLICT = "version_conflict"
    REINSTALL_NOT_ALLOWED = "reinstall_not_allowed"
    INVALID_PLAN = "invalid_plan"
    INVALID_STATE = "invalid_state"
    TRANSACTION_FAILED = "transaction_failed"
    VERIFICATION_FAILED = "verification_failed"
    ROLLBACK_FAILED = "rollback_failed"
    INSTALLATION_CANCELLED = "installation_cancelled"


class InstallationEventType(str, Enum):
    PLANNED = "planned"
    STARTED = "started"
    STEP_COMPLETED = "step_completed"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLBACK_STARTED = "rollback_started"
    ROLLED_BACK = "rolled_back"
    CLEARED = "cleared"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class InstallationId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Installation id must not be empty.")

    def __str__(self) -> str:
        return self.value


InstallationCoordinate = DependencyCoordinate


@dataclass(frozen=True, slots=True)
class InstallationRequest:
    installation_id: InstallationId
    resolution_result: ResolutionResult
    requested_roots: tuple[DependencyCoordinate, ...] = ()
    strategy: InstallationStrategy = InstallationStrategy.FRESH
    allow_reinstall: bool = False
    allow_upgrade: bool = False
    allow_downgrade: bool = False
    allow_prerelease: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "requested_roots", tuple(self.requested_roots))
        object.__setattr__(self, "metadata", _map(self.metadata))
        if self.resolution_result.status is not ResolutionStatus.RESOLVED:
            raise ValueError("Installation requires a resolved ResolutionResult.")


@dataclass(frozen=True, slots=True)
class InstallationStep:
    type: InstallationStepType
    coordinate: InstallationCoordinate | None = None


@dataclass(frozen=True, slots=True)
class InstallationIssue:
    code: InstallationIssueCode
    message: str
    installation_id: InstallationId
    coordinate: InstallationCoordinate | None = None


@dataclass(frozen=True, slots=True)
class InstallationPlan:
    installation_id: InstallationId
    selected_coordinates: tuple[InstallationCoordinate, ...]
    dependency_order: tuple[InstallationCoordinate, ...]
    steps: tuple[InstallationStep, ...]
    strategy: InstallationStrategy
    issues: tuple[InstallationIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class InstalledPackageRecord:
    coordinate: InstallationCoordinate
    installation_id: InstallationId


@dataclass(frozen=True, slots=True)
class InstallationSession:
    installation_id: InstallationId
    status: InstallationStatus
    plan: InstallationPlan
    issues: tuple[InstallationIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class InstallationResult:
    session: InstallationSession
    installed: tuple[InstalledPackageRecord, ...] = ()


@dataclass(frozen=True, slots=True)
class InstallationEvent:
    sequence: int
    event_type: InstallationEventType
    installation_id: InstallationId


@dataclass(frozen=True, slots=True)
class InstallationSnapshot:
    sessions: tuple[InstallationSession, ...] = ()
    installed_records: tuple[InstalledPackageRecord, ...] = ()
    closed: bool = False
