"""Enterprise publishing workflow, queue, scheduler, approvals and recovery."""

from __future__ import annotations

from datetime import timedelta
from time import monotonic
from typing import Any

from .adapters import (
    AllowPolicyPort,
    AuditPort,
    InMemoryAuditPort,
    MockPublisherPort,
    NullReferencePort,
    PolicyPort,
    PublisherPort,
    ReferencePort,
)
from .metrics import PublishingMetrics
from .models import (
    Approval,
    ApprovalState,
    FailureCategory,
    FailureRecord,
    HistoryEntry,
    PublishingJob,
    PublishingScope,
    PublishingStatus,
    ScheduleMode,
    utcnow,
)


class TikTokPublishingCenter:
    """Tenant-isolated publishing control plane using injected platform ports."""

    def __init__(
        self,
        *,
        content: ReferencePort | None = None,
        accounts: ReferencePort | None = None,
        publisher: PublisherPort | None = None,
        proxy_policy: PolicyPort | None = None,
        farming_policy: PolicyPort | None = None,
        audit: AuditPort | None = None,
        concurrency_limit: int = 5,
        approval_required: bool = True,
    ) -> None:
        if not 1 <= concurrency_limit <= 100:
            raise ValueError("Concurrency limit must be within [1, 100].")
        self.content = content or NullReferencePort()
        self.accounts = accounts or NullReferencePort()
        self.publisher = publisher or MockPublisherPort()
        self.proxy_policy = proxy_policy or AllowPolicyPort()
        self.farming_policy = farming_policy or AllowPolicyPort()
        self.audit_port = audit or InMemoryAuditPort()
        self.concurrency_limit = concurrency_limit
        self.approval_required = approval_required
        self.jobs: dict[str, PublishingJob] = {}
        self.approvals: dict[str, Approval] = {}
        self.history: list[HistoryEntry] = []
        self.failures: list[FailureRecord] = []
        self.notifications: list[dict[str, Any]] = []
        self.metrics = PublishingMetrics()

    @staticmethod
    def _require(scope: PublishingScope, action: str) -> None:
        permission = f"tiktok:publishing:{action}"
        if (
            permission not in scope.permissions
            and "tiktok:publishing:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(job: PublishingJob, scope: PublishingScope) -> None:
        if job.tenant != scope.tenant or job.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _event(
        self,
        job: PublishingJob,
        scope: PublishingScope,
        event: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        safe_details = {
            key: value
            for key, value in (details or {}).items()
            if key.casefold() not in {"password", "secret", "token", "cookie"}
        }
        entry = HistoryEntry(
            job.id, job.status, scope.actor, job.version, event, details=safe_details
        )
        self.history.append(entry)
        self.audit_port.record(
            {
                "event": event,
                "job": job.id,
                "tenant": scope.tenant,
                "workspace": scope.workspace,
                "operator": scope.actor,
                "version": job.version,
                "timestamp": entry.timestamp.isoformat(),
            }
        )

    def _transition(
        self, job: PublishingJob, status: PublishingStatus, scope: PublishingScope
    ) -> PublishingJob:
        self._scoped(job, scope)
        allowed = {
            PublishingStatus.DRAFT: {
                PublishingStatus.APPROVED,
                PublishingStatus.CANCELLED,
                PublishingStatus.DELETED,
            },
            PublishingStatus.APPROVED: {
                PublishingStatus.QUEUED,
                PublishingStatus.SCHEDULED,
                PublishingStatus.CANCELLED,
            },
            PublishingStatus.QUEUED: {
                PublishingStatus.PUBLISHING,
                PublishingStatus.PAUSED,
                PublishingStatus.CANCELLED,
            },
            PublishingStatus.SCHEDULED: {
                PublishingStatus.QUEUED,
                PublishingStatus.PAUSED,
                PublishingStatus.CANCELLED,
            },
            PublishingStatus.PUBLISHING: {
                PublishingStatus.PUBLISHED,
                PublishingStatus.FAILED,
                PublishingStatus.CANCELLED,
            },
            PublishingStatus.FAILED: {
                PublishingStatus.QUEUED,
                PublishingStatus.PAUSED,
                PublishingStatus.ARCHIVED,
            },
            PublishingStatus.PAUSED: {
                PublishingStatus.QUEUED,
                PublishingStatus.SCHEDULED,
                PublishingStatus.CANCELLED,
            },
            PublishingStatus.CANCELLED: {PublishingStatus.ARCHIVED},
            PublishingStatus.PUBLISHED: {PublishingStatus.ARCHIVED},
            PublishingStatus.ARCHIVED: {PublishingStatus.DELETED},
            PublishingStatus.DELETED: set(),
        }
        if status not in allowed[job.status]:
            raise ValueError(
                f"Invalid transition: {job.status.value} -> {status.value}"
            )
        job.status = status
        job.version += 1
        job.updated_at = utcnow()
        self._event(job, scope, f"job.{status.value}")
        return job

    def create_job(self, job: PublishingJob, scope: PublishingScope) -> PublishingJob:
        self._require(scope, "write")
        self._scoped(job, scope)
        job.validate()
        if job.id in self.jobs:
            raise ValueError("Publishing job ID must be unique.")
        if not self.content.validate(job.project_reference, job.tenant, job.workspace):
            raise ValueError("Project reference is invalid.")
        if not self.accounts.validate(job.account_reference, job.tenant, job.workspace):
            raise ValueError("Account reference is invalid.")
        self.jobs[job.id] = job
        self.metrics.increment("tiktok_publish_jobs_total")
        self._event(job, scope, "job.created")
        if self.approval_required:
            self.approvals[job.id] = Approval(job.id, "")
            self._notify(job, "approval_required")
        return job

    def list_jobs(self, scope: PublishingScope) -> list[PublishingJob]:
        self._require(scope, "read")
        return [
            job
            for job in self.jobs.values()
            if job.tenant == scope.tenant
            and job.workspace == scope.workspace
            and job.status is not PublishingStatus.DELETED
        ]

    def review(
        self,
        job_reference: str,
        scope: PublishingScope,
        *,
        approve: bool,
        notes: str = "",
        expires_at: Any = None,
    ) -> Approval:
        self._require(scope, "approve")
        job = self.jobs[job_reference]
        self._scoped(job, scope)
        approval = self.approvals.setdefault(job.id, Approval(job.id, scope.actor))
        approval.reviewer = scope.actor
        approval.notes = notes
        approval.expires_at = expires_at
        approval.reviewed_at = utcnow()
        approval.version += 1
        approval.state = ApprovalState.APPROVED if approve else ApprovalState.REJECTED
        if approve:
            if job.status is PublishingStatus.DRAFT:
                self._transition(job, PublishingStatus.APPROVED, scope)
            elif job.status is PublishingStatus.APPROVED:
                job.version += 1
                job.updated_at = utcnow()
                self._event(job, scope, "approval.reapproved", {"notes": notes})
            else:
                raise ValueError(
                    "Only draft or previously approved jobs can be approved."
                )
        else:
            self._event(job, scope, "approval.rejected", {"notes": notes})
        return approval

    def expire_approvals(self, scope: PublishingScope) -> int:
        self._require(scope, "approve")
        count = 0
        now = utcnow()
        for approval in self.approvals.values():
            job = self.jobs[approval.job_reference]
            if (
                job.tenant == scope.tenant
                and job.workspace == scope.workspace
                and approval.expires_at
                and approval.expires_at <= now
                and approval.state is ApprovalState.APPROVED
            ):
                approval.state = ApprovalState.EXPIRED
                approval.version += 1
                count += 1
                self._event(job, scope, "approval.expired")
        return count

    def enqueue(self, job_reference: str, scope: PublishingScope) -> PublishingJob:
        self._require(scope, "queue")
        job = self.jobs[job_reference]
        self._scoped(job, scope)
        approval = self.approvals.get(job.id)
        if self.approval_required and (
            approval is None or approval.state is not ApprovalState.APPROVED
        ):
            raise PermissionError("An active publishing approval is required.")
        target = (
            PublishingStatus.QUEUED
            if job.schedule.mode is ScheduleMode.IMMEDIATE
            else PublishingStatus.SCHEDULED
        )
        self._transition(job, target, scope)
        self.metrics.increment("tiktok_publish_queue_total")
        return job

    def queue(
        self, scope: PublishingScope, *, kind: str = "priority"
    ) -> list[PublishingJob]:
        self._require(scope, "read")
        jobs = [
            job
            for job in self.list_jobs(scope)
            if job.status
            in {
                PublishingStatus.QUEUED,
                PublishingStatus.SCHEDULED,
                PublishingStatus.FAILED,
            }
        ]
        if kind == "fifo":
            return sorted(jobs, key=lambda item: item.created_at)
        if kind == "account":
            return sorted(
                jobs, key=lambda item: (item.account_reference, -item.priority)
            )
        if kind == "workspace":
            return sorted(jobs, key=lambda item: (item.workspace, -item.priority))
        if kind == "retry":
            return sorted(
                (item for item in jobs if item.attempts > 0),
                key=lambda item: item.next_attempt_at or item.updated_at,
            )
        if kind == "delayed":
            return sorted(
                (item for item in jobs if item.next_attempt_at),
                key=lambda item: item.next_attempt_at or item.updated_at,
            )
        return sorted(jobs, key=lambda item: (-item.priority, item.created_at))

    def tick(self, scope: PublishingScope) -> list[PublishingJob]:
        self._require(scope, "execute")
        now = utcnow()
        for job in self.list_jobs(scope):
            if (
                job.status is PublishingStatus.SCHEDULED
                and job.schedule.run_at
                and job.schedule.run_at <= now
            ):
                self._transition(job, PublishingStatus.QUEUED, scope)
        active = sum(
            job.status is PublishingStatus.PUBLISHING for job in self.list_jobs(scope)
        )
        capacity = max(0, self.concurrency_limit - active)
        completed: list[PublishingJob] = []
        for job in self.queue(scope)[:capacity]:
            if job.next_attempt_at and job.next_attempt_at > now:
                continue
            completed.append(self.execute(job.id, scope))
        if not self.queue(scope):
            self.notifications.append(
                {
                    "type": "queue_complete",
                    "tenant": scope.tenant,
                    "workspace": scope.workspace,
                }
            )
        return completed

    def execute(self, job_reference: str, scope: PublishingScope) -> PublishingJob:
        self._require(scope, "execute")
        job = self.jobs[job_reference]
        self._scoped(job, scope)
        if job.status is not PublishingStatus.QUEUED:
            raise ValueError("Only queued jobs can be published.")
        if not self.proxy_policy.allowed(
            job.account_reference, job.tenant, job.workspace
        ):
            return self.fail(job.id, FailureCategory.PROXY, "Proxy unavailable", scope)
        if not self.farming_policy.allowed(
            job.account_reference, job.tenant, job.workspace
        ):
            return self.fail(
                job.id, FailureCategory.SESSION, "Account unavailable", scope
            )
        self._transition(job, PublishingStatus.PUBLISHING, scope)
        job.attempts += 1
        started = monotonic()
        try:
            succeeded = self.publisher.publish(job)
        except TimeoutError:
            return self.fail(
                job.id, FailureCategory.TIMEOUT, "Publishing timed out", scope
            )
        except Exception:
            return self.fail(job.id, FailureCategory.BROWSER, "Publisher failed", scope)
        self.metrics.observe("tiktok_publish_latency_seconds", monotonic() - started)
        if not succeeded:
            return self.fail(
                job.id, FailureCategory.BROWSER, "Publisher rejected job", scope
            )
        self._transition(job, PublishingStatus.PUBLISHED, scope)
        self.metrics.increment("tiktok_publish_success_total")
        self._notify(job, "success")
        return job

    def fail(
        self,
        job_reference: str,
        category: FailureCategory,
        message: str,
        scope: PublishingScope,
    ) -> PublishingJob:
        job = self.jobs[job_reference]
        self._scoped(job, scope)
        if job.status is not PublishingStatus.PUBLISHING:
            self._transition(job, PublishingStatus.PUBLISHING, scope)
        self._transition(job, PublishingStatus.FAILED, scope)
        recoverable = category in job.retry_policy.retryable_categories
        self.failures.append(FailureRecord(job.id, category, message, recoverable))
        self.metrics.increment("tiktok_publish_failure_total")
        self._notify(job, "failure")
        if (
            recoverable
            and job.retry_policy.auto_retry
            and job.attempts < job.retry_policy.maximum_attempts
        ):
            self.retry(job.id, scope, manual=False)
        else:
            self._notify(job, "retry_required")
        return job

    def retry(
        self, job_reference: str, scope: PublishingScope, *, manual: bool = True
    ) -> PublishingJob:
        self._require(scope, "retry" if manual else "execute")
        job = self.jobs[job_reference]
        self._scoped(job, scope)
        if job.status is not PublishingStatus.FAILED:
            raise ValueError("Only failed jobs can be retried.")
        if job.attempts >= job.retry_policy.maximum_attempts:
            raise ValueError("Maximum retry attempts reached.")
        job.next_attempt_at = utcnow() + timedelta(
            seconds=job.retry_policy.delay_for(job.attempts)
        )
        self._transition(job, PublishingStatus.QUEUED, scope)
        self.metrics.increment("tiktok_publish_retry_total")
        self._event(job, scope, "retry.manual" if manual else "retry.automatic")
        return job

    def recover(self, job_reference: str, scope: PublishingScope) -> FailureRecord:
        self._require(scope, "recover")
        job = self.jobs[job_reference]
        self._scoped(job, scope)
        failure = next(
            item
            for item in reversed(self.failures)
            if item.job_reference == job_reference and item.recovered_at is None
        )
        failure.recovered_at = utcnow()
        failure.recovered_by = scope.actor
        self._event(job, scope, "failure.recovered")
        return failure

    def pause(self, job_reference: str, scope: PublishingScope) -> PublishingJob:
        self._require(scope, "write")
        return self._transition(
            self.jobs[job_reference], PublishingStatus.PAUSED, scope
        )

    def cancel(self, job_reference: str, scope: PublishingScope) -> PublishingJob:
        self._require(scope, "write")
        job = self._transition(
            self.jobs[job_reference], PublishingStatus.CANCELLED, scope
        )
        self._notify(job, "cancellation")
        return job

    def archive(self, job_reference: str, scope: PublishingScope) -> PublishingJob:
        self._require(scope, "write")
        return self._transition(
            self.jobs[job_reference], PublishingStatus.ARCHIVED, scope
        )

    def delete(self, job_reference: str, scope: PublishingScope) -> PublishingJob:
        self._require(scope, "delete")
        return self._transition(
            self.jobs[job_reference], PublishingStatus.DELETED, scope
        )

    def _notify(self, job: PublishingJob, kind: str) -> None:
        self.notifications.append(
            {
                "type": kind,
                "job": job.id,
                "tenant": job.tenant,
                "workspace": job.workspace,
                "dashboard": True,
            }
        )

    def analytics(self, scope: PublishingScope) -> dict[str, Any]:
        jobs = self.list_jobs(scope)
        published = sum(job.status is PublishingStatus.PUBLISHED for job in jobs)
        failed = sum(job.status is PublishingStatus.FAILED for job in jobs)
        total = len(jobs)
        queue_times = [
            (entry.timestamp - job.created_at).total_seconds()
            for job in jobs
            for entry in self.history
            if entry.job_reference == job.id and entry.event == "job.publishing"
        ]
        return {
            "publishing_volume": total,
            "success_rate": published / total if total else 0.0,
            "failure_rate": failed / total if total else 0.0,
            "retry_count": int(self.metrics.values["tiktok_publish_retry_total"]),
            "average_queue_time_seconds": (
                sum(queue_times) / len(queue_times) if queue_times else 0.0
            ),
            "execution_time_seconds": self.metrics.values[
                "tiktok_publish_latency_seconds"
            ],
            "daily_report": {"published": published, "failed": failed},
        }

    def dashboard(self, scope: PublishingScope) -> dict[str, Any]:
        jobs = self.list_jobs(scope)
        job_ids = {job.id for job in jobs}
        return {
            "queue": [item.to_dict() for item in self.queue(scope)],
            "calendar": [
                item.to_dict()
                for item in jobs
                if item.schedule.mode is not ScheduleMode.IMMEDIATE
            ],
            "schedules": [
                item.to_dict()
                for item in jobs
                if item.status is PublishingStatus.SCHEDULED
            ],
            "approvals": [
                item for key, item in self.approvals.items() if key in job_ids
            ],
            "failures": [
                item for item in self.failures if item.job_reference in job_ids
            ],
            "retries": [item.to_dict() for item in jobs if item.attempts > 0],
            "history": [item for item in self.history if item.job_reference in job_ids],
            "analytics": self.analytics(scope),
            "statistics": self.metrics.snapshot(),
            "notifications": [
                item
                for item in self.notifications
                if item.get("tenant") == scope.tenant
                and item.get("workspace") == scope.workspace
            ],
        }
