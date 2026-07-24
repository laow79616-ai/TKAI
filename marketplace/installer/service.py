"""Thread-safe pure-memory reference installer; no package mutation occurs."""

from __future__ import annotations

from threading import RLock

from .errors import InstallerClosedError, InstallerConflictError, InstallerNotFoundError
from .lifecycle import InstallationLifecycle
from .models import (
    InstallationCoordinate,
    InstallationId,
    InstallationPlan,
    InstallationRequest,
    InstallationResult,
    InstallationSession,
    InstallationSnapshot,
    InstallationStatus,
    InstallationStep,
    InstallationStepType,
    InstallationStrategy,
    InstalledPackageRecord,
)
from .source import ReferenceResolutionInstallationSource


class ReferenceInstallationStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._items: dict[InstallationCoordinate, InstalledPackageRecord] = {}
        self._closed = False

    def add(self, item: InstalledPackageRecord) -> None:
        with self._lock:
            if self._closed:
                raise InstallerClosedError("Installation store is closed.")
            if item.coordinate in self._items:
                raise ValueError("Package is already installed.")
            self._items[item.coordinate] = item

    def remove(self, c: InstallationCoordinate) -> None:
        with self._lock:
            if self._closed:
                raise InstallerClosedError("Installation store is closed.")
            if c not in self._items:
                raise InstallerNotFoundError("Installed package was not found.")
            del self._items[c]

    def get(self, c: InstallationCoordinate) -> InstalledPackageRecord:
        with self._lock:
            try:
                return self._items[c]
            except KeyError as exc:
                raise InstallerNotFoundError(
                    "Installed package was not found."
                ) from exc

    def exists(self, c: InstallationCoordinate) -> bool:
        with self._lock:
            return c in self._items

    def snapshot(self) -> tuple[InstalledPackageRecord, ...]:
        return self.list()

    def clear(self) -> None:
        with self._lock:
            if self._closed:
                raise InstallerClosedError("Installation store is closed.")
            self._items.clear()

    def list(self) -> tuple[InstalledPackageRecord, ...]:
        return tuple(self._items[k] for k in sorted(self._items, key=lambda x: x.key()))

    def close(self) -> None:
        with self._lock:
            self._closed = True


class ReferenceInstallerService:
    def __init__(self, store: ReferenceInstallationStore | None = None) -> None:
        self._lock = RLock()
        self.store = store or ReferenceInstallationStore()
        self._sessions: dict[str, InstallationSession] = {}
        self._closed = False
        self._lifecycle = InstallationLifecycle()

    def plan(self, r: InstallationRequest) -> InstallationPlan:
        self._open()
        source = ReferenceResolutionInstallationSource(r.resolution_result)
        if r.requested_roots and tuple(r.requested_roots) != source.coordinates():
            raise ValueError("Requested roots must match resolved coordinates.")
        steps = (
            InstallationStep(InstallationStepType.VALIDATE),
            InstallationStep(InstallationStepType.PREPARE),
            *(
                InstallationStep(InstallationStepType.INSTALL, c)
                for c in source.dependency_order()
            ),
            InstallationStep(InstallationStepType.FINALIZE),
        )
        return InstallationPlan(
            r.installation_id,
            source.coordinates(),
            source.dependency_order(),
            steps,
            r.strategy,
        )

    def install(self, r: InstallationRequest) -> InstallationResult:
        with self._lock:
            p = self.plan(r)
            records = tuple(
                InstalledPackageRecord(c, r.installation_id) for c in p.dependency_order
            )
            if r.strategy is not InstallationStrategy.DRY_RUN:
                existing = set(x.coordinate for x in self.store.list())
                if (
                    any(x.coordinate in existing for x in records)
                    and not r.allow_reinstall
                ):
                    raise InstallerConflictError("Package is already installed.")
                for x in records:
                    if x.coordinate not in existing:
                        self.store.add(x)
            self._lifecycle.transition(
                InstallationStatus.PENDING, InstallationStatus.PLANNED
            )
            self._lifecycle.transition(
                InstallationStatus.PLANNED, InstallationStatus.RUNNING
            )
            s = InstallationSession(r.installation_id, InstallationStatus.SUCCEEDED, p)
            self._sessions[str(r.installation_id)] = s
            return InstallationResult(s, records)

    def cancel(self, i: InstallationId | str) -> InstallationSession:
        with self._lock:
            self._open()
            try:
                current = self._sessions[str(i)]
            except KeyError as exc:
                raise InstallerNotFoundError(
                    "Installation session was not found."
                ) from exc
            session = InstallationSession(
                current.installation_id, InstallationStatus.CANCELLED, current.plan
            )
            self._sessions[str(i)] = session
            return session

    def get(self, i: InstallationId | str) -> InstallationSession:
        try:
            return self._sessions[str(i)]
        except KeyError as exc:
            raise InstallerNotFoundError("Installation session was not found.") from exc

    def list(self) -> tuple[InstallationSession, ...]:
        return tuple(self._sessions[key] for key in sorted(self._sessions))

    def snapshot(self) -> InstallationSnapshot:
        return InstallationSnapshot(
            tuple(self._sessions[k] for k in sorted(self._sessions)),
            self.store.list(),
            self._closed,
        )

    def clear(self) -> None:
        self._open()
        self._sessions.clear()
        self.store.clear()

    def close(self) -> None:
        self._closed = True

    def _open(self) -> None:
        if self._closed:
            raise InstallerClosedError("Installer service is closed.")
