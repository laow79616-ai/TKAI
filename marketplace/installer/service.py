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
from .reliability import (
    InstallationStatistics,
    InstallationTransaction,
    InstallationTransactionState,
    ReferenceInstallationVerifier,
    RollbackPlan,
    RollbackResult,
    RollbackState,
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
        self._transactions: dict[str, InstallationTransaction] = {}
        self._rollbacks: list[RollbackResult] = []
        self._events = []
        self._verifier = ReferenceInstallationVerifier()

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
            self._emit("planned", r.installation_id)
            self._emit("started", r.installation_id)
            self._transactions[str(r.installation_id)] = InstallationTransaction(
                r.installation_id, InstallationTransactionState.CREATED
            )
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
                self._transactions[str(r.installation_id)] = InstallationTransaction(
                    r.installation_id, InstallationTransactionState.PREPARED
                )
                added = []
                try:
                    for x in records:
                        if x.coordinate not in existing:
                            self.store.add(x)
                            added.append(x.coordinate)
                except Exception:
                    for coordinate in added:
                        self.store.remove(coordinate)
                    self._transactions[str(r.installation_id)] = (
                        InstallationTransaction(
                            r.installation_id, InstallationTransactionState.ABORTED
                        )
                    )
                    self._emit("failed", r.installation_id)
                    raise
            self._lifecycle.transition(
                InstallationStatus.PENDING, InstallationStatus.PLANNED
            )
            self._lifecycle.transition(
                InstallationStatus.PLANNED, InstallationStatus.RUNNING
            )
            s = InstallationSession(r.installation_id, InstallationStatus.SUCCEEDED, p)
            self._sessions[str(r.installation_id)] = s
            if not self._verifier.verify(p, InstallationResult(s, records), records):
                self._transactions[str(r.installation_id)] = InstallationTransaction(
                    r.installation_id, InstallationTransactionState.ABORTED
                )
                raise RuntimeError("Installation verification failed.")
            self._transactions[str(r.installation_id)] = InstallationTransaction(
                r.installation_id, InstallationTransactionState.COMMITTED
            )
            self._emit("completed", r.installation_id)
            return InstallationResult(s, records)

    def rollback(self, i: InstallationId | str) -> RollbackResult:
        with self._lock:
            self._open()
            session = self.get(i)
            records = tuple(
                InstalledPackageRecord(c, session.installation_id)
                for c in session.plan.dependency_order
            )
            plan = RollbackPlan(session.installation_id, records)
            self._emit("rollback_started", session.installation_id)
            for record in records:
                if self.store.exists(record.coordinate):
                    self.store.remove(record.coordinate)
            self._sessions[str(i)] = InstallationSession(
                session.installation_id, InstallationStatus.ROLLED_BACK, session.plan
            )
            result = RollbackResult(plan, RollbackState.COMPLETED)
            self._rollbacks.append(result)
            self._transactions[str(i)] = InstallationTransaction(
                session.installation_id, InstallationTransactionState.ROLLED_BACK
            )
            self._emit("rolled_back", session.installation_id)
            return result

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
        sessions = tuple(self._sessions[k] for k in sorted(self._sessions))
        records = self.store.list()
        return InstallationSnapshot(
            sessions,
            records,
            tuple(self._events),
            tuple(self._transactions[k] for k in sorted(self._transactions)),
            tuple(self._rollbacks),
            self._statistics(sessions, records),
            self._closed,
        )

    def clear(self) -> None:
        self._open()
        self._sessions.clear()
        self.store.clear()

    def close(self) -> None:
        self._closed = True
        self._emit("closed", InstallationId("service"))

    def _open(self) -> None:
        if self._closed:
            raise InstallerClosedError("Installer service is closed.")

    def _emit(self, event_type: str, installation_id: InstallationId) -> None:
        from .models import InstallationEvent, InstallationEventType

        self._events.append(
            InstallationEvent(
                len(self._events) + 1,
                InstallationEventType(event_type),
                installation_id,
            )
        )

    @staticmethod
    def _statistics(sessions, records):
        counts = {
            status: sum(item.status is status for item in sessions)
            for status in InstallationStatus
        }
        return InstallationStatistics(
            len(sessions),
            counts[InstallationStatus.SUCCEEDED],
            counts[InstallationStatus.FAILED],
            counts[InstallationStatus.CANCELLED],
            counts[InstallationStatus.ROLLED_BACK],
            len(records),
            len({x.coordinate.publisher_id for x in records}),
            len({str(x.coordinate.version) for x in records}),
        )
