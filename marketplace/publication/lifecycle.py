"""Deterministic local publication lifecycle transitions."""

from __future__ import annotations

from .errors import PublicationStateError
from .models import PublicationStatus


class PublicationLifecycle:
    """Validate status changes without mutating a publication snapshot."""

    _TRANSITIONS: dict[PublicationStatus, frozenset[PublicationStatus]] = {
        PublicationStatus.DRAFT: frozenset(
            {PublicationStatus.SUBMITTED, PublicationStatus.WITHDRAWN}
        ),
        PublicationStatus.SUBMITTED: frozenset(
            {PublicationStatus.VALIDATING, PublicationStatus.WITHDRAWN}
        ),
        PublicationStatus.VALIDATING: frozenset(
            {PublicationStatus.ACCEPTED, PublicationStatus.REJECTED}
        ),
        PublicationStatus.REJECTED: frozenset({PublicationStatus.SUBMITTED}),
        PublicationStatus.ACCEPTED: frozenset(),
        PublicationStatus.WITHDRAWN: frozenset(),
    }

    def can_transition(
        self, current: PublicationStatus, target: PublicationStatus
    ) -> bool:
        """Return whether an explicit target transition is permitted."""
        return target in self._TRANSITIONS[current]

    def allowed_transitions(
        self, current: PublicationStatus
    ) -> tuple[PublicationStatus, ...]:
        """Return permitted targets in stable value order."""
        return tuple(
            sorted(self._TRANSITIONS[current], key=lambda status: status.value)
        )

    def transition(
        self, current: PublicationStatus, target: PublicationStatus
    ) -> PublicationStatus:
        """Return target or raise a stable error without changing any object."""
        if not self.can_transition(current, target):
            raise PublicationStateError(
                f"Illegal publication transition: {current.value} -> {target.value}"
            )
        return target
