"""Thread-safe in-memory Reference Publication Service with no catalog integration."""

from __future__ import annotations

from threading import RLock

from ..publisher import Publisher
from .errors import (
    PublicationClosedError,
    PublicationConflictError,
    PublicationNotFoundError,
    PublicationValidationError,
)
from .lifecycle import PublicationLifecycle
from .models import (
    PublicationDecision,
    PublicationId,
    PublicationPolicy,
    PublicationRequest,
    PublicationResult,
    PublicationSnapshot,
    PublicationStatus,
)
from .validator import ReferencePublicationValidator


class ReferencePublicationService:
    """Manage local publication workflow snapshots without Registry side effects."""

    def __init__(
        self,
        publisher: Publisher,
        *,
        policy: PublicationPolicy | None = None,
        validator: ReferencePublicationValidator | None = None,
    ) -> None:
        self._lock = RLock()
        self._publisher = publisher
        self._policy = policy if policy is not None else PublicationPolicy()
        self._validator = (
            validator
            if validator is not None
            else ReferencePublicationValidator(publisher)
        )
        self._lifecycle = PublicationLifecycle()
        self._snapshots: dict[str, PublicationSnapshot] = {}
        self._coordinates: set[tuple[str, str, str]] = set()
        self._closed = False

    def submit(self, request: PublicationRequest) -> PublicationSnapshot:
        """Create a submitted local snapshot, rejecting duplicate coordinates."""
        with self._lock:
            self._ensure_open()
            if request.publisher_id != self._publisher.publisher_id:
                raise PublicationValidationError(
                    "Publication request publisher does not match this service."
                )
            identifier = str(request.publication_id)
            if identifier in self._snapshots:
                raise PublicationConflictError(identifier)
            coordinate = self._coordinate(request)
            if (
                not self._policy.allow_duplicate_coordinate
                and coordinate in self._coordinates
            ):
                raise PublicationConflictError(
                    "Duplicate publication coordinate is not allowed."
                )
            current = request.requested_status
            if current is PublicationStatus.DRAFT:
                current = self._lifecycle.transition(
                    current, PublicationStatus.SUBMITTED
                )
            elif current is not PublicationStatus.SUBMITTED:
                raise PublicationValidationError(
                    "Publication request status must be draft or submitted."
                )
            snapshot = PublicationSnapshot(request, current)
            self._snapshots[identifier] = snapshot
            self._coordinates.add(coordinate)
            return snapshot

    def validate(self, publication_id: PublicationIdLike) -> PublicationResult:
        """Run deterministic local validation and retain a validating snapshot."""
        with self._lock:
            self._ensure_open()
            snapshot = self._get(publication_id)
            status = self._lifecycle.transition(
                snapshot.status, PublicationStatus.VALIDATING
            )
            result = self._validator.validate(snapshot.request, self._policy)
            result = PublicationResult(
                result.publication_id, status, result.decision, result.issues
            )
            self._snapshots[str(snapshot.publication_id)] = PublicationSnapshot(
                snapshot.request, status, result
            )
            return result

    def accept(self, publication_id: PublicationIdLike) -> PublicationSnapshot:
        """Accept a validating request only after a local accept decision."""
        with self._lock:
            self._ensure_open()
            snapshot = self._get(publication_id)
            if (
                snapshot.result is None
                or snapshot.result.decision is not PublicationDecision.ACCEPT
            ):
                raise PublicationValidationError(
                    "Publication cannot be accepted without a local accept decision."
                )
            return self._transition(snapshot, PublicationStatus.ACCEPTED)

    def reject(self, publication_id: PublicationIdLike) -> PublicationSnapshot:
        """Reject a validating request without modifying any package catalog state."""
        with self._lock:
            self._ensure_open()
            return self._transition(
                self._get(publication_id), PublicationStatus.REJECTED
            )

    def withdraw(self, publication_id: PublicationIdLike) -> PublicationSnapshot:
        """Withdraw a draft or submitted request using the local lifecycle only."""
        with self._lock:
            self._ensure_open()
            return self._transition(
                self._get(publication_id), PublicationStatus.WITHDRAWN
            )

    def get(self, publication_id: PublicationIdLike) -> PublicationSnapshot:
        """Return a stable immutable local publication snapshot."""
        with self._lock:
            self._ensure_open()
            return self._get(publication_id)

    def list(self) -> tuple[PublicationSnapshot, ...]:
        """Return all local snapshots in stable publication-id order."""
        with self._lock:
            self._ensure_open()
            return tuple(snapshot for _, snapshot in sorted(self._snapshots.items()))

    def snapshot(self) -> tuple[PublicationSnapshot, ...]:
        """Return a stable read-only snapshot of local publication workflow state."""
        return self.list()

    def clear(self) -> None:
        """Clear local workflow descriptions without modifying a package catalog."""
        with self._lock:
            self._ensure_open()
            self._snapshots.clear()
            self._coordinates.clear()

    def close(self) -> None:
        """Idempotently release in-memory state; later operations raise clearly."""
        with self._lock:
            if self._closed:
                return
            self._snapshots.clear()
            self._coordinates.clear()
            self._closed = True

    def _transition(
        self, snapshot: PublicationSnapshot, target: PublicationStatus
    ) -> PublicationSnapshot:
        status = self._lifecycle.transition(snapshot.status, target)
        result = snapshot.result
        if result is not None:
            result = PublicationResult(
                result.publication_id, status, result.decision, result.issues
            )
        updated = PublicationSnapshot(snapshot.request, status, result)
        self._snapshots[str(snapshot.publication_id)] = updated
        return updated

    def _get(self, publication_id: PublicationIdLike) -> PublicationSnapshot:
        identifier = str(publication_id)
        try:
            return self._snapshots[identifier]
        except KeyError as exc:
            raise PublicationNotFoundError(identifier) from exc

    @staticmethod
    def _coordinate(request: PublicationRequest) -> tuple[str, str, str]:
        return (
            request.publisher_id,
            request.package_manifest.package_id,
            str(request.package_manifest.version),
        )

    def _ensure_open(self) -> None:
        if self._closed:
            raise PublicationClosedError("Reference publication service is closed.")


PublicationIdLike = PublicationId | str
