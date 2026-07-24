"""Read-only pure-memory reference verification and trust services."""

from __future__ import annotations

from threading import RLock

from .models import (
    TrustDecision,
    TrustLevel,
    TrustPolicy,
    TrustReport,
    TrustSnapshot,
    TrustStatistics,
    VerificationIssue,
    VerificationIssueCode,
    VerificationReport,
    VerificationRequest,
    VerificationResult,
    VerificationSnapshot,
    VerificationStatistics,
    VerificationStatus,
)


class ReferenceVerificationService:
    def __init__(self) -> None:
        self._lock = RLock()
        self._reports = []
        self._closed = False

    def verify(self, request: VerificationRequest) -> VerificationReport:
        with self._lock:
            if self._closed:
                raise RuntimeError("Verification service is closed.")
            issues = (
                ()
                if request.subject is not None
                else (
                    VerificationIssue(
                        VerificationIssueCode.MISSING_MANIFEST,
                        "Verification subject is required.",
                    ),
                )
            )
            report = VerificationReport(
                request,
                VerificationResult(
                    (
                        VerificationStatus.PASSED
                        if not issues
                        else VerificationStatus.FAILED
                    ),
                    issues,
                ),
            )
            self._reports.append(report)
            return report

    def report(self):
        return tuple(self._reports)

    def snapshot(self):
        reports = tuple(self._reports)
        return VerificationSnapshot(
            reports,
            VerificationStatistics(
                len(reports),
                sum(x.result.status is VerificationStatus.PASSED for x in reports),
                sum(x.result.status is VerificationStatus.WARNING for x in reports),
                sum(x.result.status is VerificationStatus.FAILED for x in reports),
            ),
            self._closed,
        )

    def clear(self):
        self._reports.clear()

    def close(self):
        self._closed = True


class ReferenceTrustService:
    def __init__(self, policy: TrustPolicy | None = None) -> None:
        self._policy = policy or TrustPolicy()
        self._reports = []
        self._closed = False

    def evaluate(self, level: TrustLevel) -> TrustReport:
        if self._closed:
            raise RuntimeError("Trust service is closed.")
        order = list(TrustLevel)
        decision = (
            TrustDecision.ALLOW
            if order.index(level) >= order.index(self._policy.minimum)
            else TrustDecision.REVIEW
        )
        report = TrustReport(level, decision, self._policy)
        self._reports.append(report)
        return report

    def report(self):
        return tuple(self._reports)

    def snapshot(self):
        reports = tuple(self._reports)
        return TrustSnapshot(
            reports,
            TrustStatistics(
                len(reports),
                sum(x.decision is TrustDecision.ALLOW for x in reports),
                sum(x.decision is TrustDecision.REJECT for x in reports),
                sum(x.decision is TrustDecision.REVIEW for x in reports),
            ),
            self._closed,
        )

    def clear(self):
        self._reports.clear()

    def close(self):
        self._closed = True
