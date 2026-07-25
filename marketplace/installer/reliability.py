"""Immutable, offline reliability models for the reference installer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import (
    InstallationId,
    InstallationPlan,
    InstallationResult,
    InstalledPackageRecord,
)


class InstallationTransactionState(str, Enum):
    CREATED = "created"
    PREPARED = "prepared"
    COMMITTED = "committed"
    ABORTED = "aborted"
    ROLLED_BACK = "rolled_back"


@dataclass(frozen=True, slots=True)
class InstallationTransaction:
    installation_id: InstallationId
    state: InstallationTransactionState = InstallationTransactionState.CREATED


class RollbackState(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class RollbackStrategy(str, Enum):
    REMOVE_RECORDS = "remove_records"


@dataclass(frozen=True, slots=True)
class RollbackPlan:
    installation_id: InstallationId
    records: tuple[InstalledPackageRecord, ...]
    strategy: RollbackStrategy = RollbackStrategy.REMOVE_RECORDS

    def __post_init__(self) -> None:
        object.__setattr__(self, "records", tuple(self.records))


@dataclass(frozen=True, slots=True)
class RollbackResult:
    plan: RollbackPlan
    state: RollbackState


@dataclass(frozen=True, slots=True)
class InstallationStatistics:
    total_sessions: int
    succeeded: int
    failed: int
    cancelled: int
    rolled_back: int
    installed_packages: int
    installed_publishers: int
    installed_versions: int

    @property
    def success_rate(self) -> float:
        return 0.0 if not self.total_sessions else self.succeeded / self.total_sessions


class InstallationVerifier:
    def verify(
        self,
        plan: InstallationPlan,
        result: InstallationResult,
        records: tuple[InstalledPackageRecord, ...],
    ) -> bool:
        raise NotImplementedError


class ReferenceInstallationVerifier(InstallationVerifier):
    def verify(
        self,
        plan: InstallationPlan,
        result: InstallationResult,
        records: tuple[InstalledPackageRecord, ...],
    ) -> bool:
        return (
            result.session.status.value == "succeeded"
            and plan.dependency_order == tuple(item.coordinate for item in records)
            and result.installed == records
        )
