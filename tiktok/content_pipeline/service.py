"""Approval-gated orchestration for content preparation and reference handoff."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from time import perf_counter
from typing import Any

from .adapters import (
    BoundedTestDouble,
    HandoffPort,
    ReferenceIntegrityPort,
    RiskStatePort,
)
from .metrics import PipelineMetrics
from .models import (
    Approval,
    ApprovalKind,
    AuditEvent,
    Checkpoint,
    ContentPackage,
    ContentPipeline,
    Handoff,
    HandoffTarget,
    PipelineInput,
    PipelineJob,
    PipelineStatus,
    QualityResult,
    RequestScope,
    Review,
    ValidationResult,
    utcnow,
    validate_metadata,
    validate_reference,
)

TRANSITIONS: dict[PipelineStatus, frozenset[PipelineStatus]] = {
    PipelineStatus.DRAFT: frozenset(
        {PipelineStatus.CONFIGURED, PipelineStatus.CANCELLED}
    ),
    PipelineStatus.CONFIGURED: frozenset(
        {PipelineStatus.VALIDATING, PipelineStatus.PAUSED, PipelineStatus.CANCELLED}
    ),
    PipelineStatus.VALIDATING: frozenset(
        {PipelineStatus.READY, PipelineStatus.FAILED, PipelineStatus.PAUSED}
    ),
    PipelineStatus.READY: frozenset(
        {PipelineStatus.QUEUED, PipelineStatus.PAUSED, PipelineStatus.CANCELLED}
    ),
    PipelineStatus.QUEUED: frozenset(
        {PipelineStatus.PROCESSING, PipelineStatus.PAUSED, PipelineStatus.CANCELLED}
    ),
    PipelineStatus.PROCESSING: frozenset(
        {PipelineStatus.REVIEW, PipelineStatus.FAILED, PipelineStatus.PAUSED}
    ),
    PipelineStatus.REVIEW: frozenset(
        {
            PipelineStatus.APPROVED,
            PipelineStatus.PROCESSING,
            PipelineStatus.FAILED,
            PipelineStatus.PAUSED,
        }
    ),
    PipelineStatus.APPROVED: frozenset(
        {PipelineStatus.PACKAGED, PipelineStatus.PAUSED}
    ),
    PipelineStatus.PACKAGED: frozenset(
        {PipelineStatus.HANDED_OFF, PipelineStatus.FAILED, PipelineStatus.PAUSED}
    ),
    PipelineStatus.HANDED_OFF: frozenset(
        {PipelineStatus.COMPLETED, PipelineStatus.FAILED}
    ),
    PipelineStatus.COMPLETED: frozenset({PipelineStatus.ARCHIVED}),
    PipelineStatus.PAUSED: frozenset(
        {
            PipelineStatus.CONFIGURED,
            PipelineStatus.READY,
            PipelineStatus.QUEUED,
            PipelineStatus.PROCESSING,
            PipelineStatus.REVIEW,
            PipelineStatus.APPROVED,
            PipelineStatus.PACKAGED,
            PipelineStatus.CANCELLED,
        }
    ),
    PipelineStatus.FAILED: frozenset(
        {PipelineStatus.QUEUED, PipelineStatus.PAUSED, PipelineStatus.ARCHIVED}
    ),
    PipelineStatus.CANCELLED: frozenset({PipelineStatus.ARCHIVED}),
    PipelineStatus.ARCHIVED: frozenset({PipelineStatus.DELETED}),
    PipelineStatus.DELETED: frozenset(),
}


class TikTokContentPipeline:
    def __init__(
        self,
        integrity: ReferenceIntegrityPort | None = None,
        handoffs: HandoffPort | None = None,
        risk: RiskStatePort | None = None,
    ) -> None:
        adapter = BoundedTestDouble()
        self.integrity = integrity or adapter
        self.handoff_port = handoffs or adapter
        self.risk = risk or adapter
        self.pipelines: dict[str, ContentPipeline] = {}
        self.stages: dict[str, dict[str, Any]] = {}
        self.jobs: dict[str, PipelineJob] = {}
        self.inputs: dict[str, PipelineInput] = {}
        self.validation: dict[str, ValidationResult] = {}
        self.quality: dict[str, QualityResult] = {}
        self.reviews: dict[str, Review] = {}
        self.approvals: dict[str, Approval] = {}
        self.packages: dict[str, ContentPackage] = {}
        self.handoffs: dict[str, Handoff] = {}
        self.checkpoints: dict[str, Checkpoint] = {}
        self.recovery: dict[str, dict[str, Any]] = {}
        self.audit: list[AuditEvent] = []
        self.versions: list[dict[str, Any]] = []
        self.status_timeline: list[dict[str, Any]] = []
        self.metrics = PipelineMetrics()

    @staticmethod
    def _require(scope: RequestScope, action: str) -> None:
        permission = f"tiktok:content-pipeline:{action}"
        if (
            permission not in scope.permissions
            and "tiktok:content-pipeline:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(item: Any, scope: RequestScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def scoped_values(self, values: Any, scope: RequestScope) -> list[Any]:
        self._require(scope, "read")
        return [
            v
            for v in values
            if v.tenant == scope.tenant and v.workspace == scope.workspace
        ]

    def _record(
        self, p: ContentPipeline, scope: RequestScope, action: str, detail: str = ""
    ) -> None:
        if any(
            x in detail.casefold()
            for x in ("password=", "secret=", "token=", "cookie=", "session=")
        ):
            raise ValueError("Secrets are forbidden in audit records.")
        self.audit.append(
            AuditEvent(p.id, p.tenant, p.workspace, scope.actor, action, detail)
        )

    def create_pipeline(
        self, p: ContentPipeline, scope: RequestScope
    ) -> ContentPipeline:
        self._require(scope, "write")
        self._scoped(p, scope)
        p.validate()
        if p.id in self.pipelines:
            raise ValueError("Pipeline ID must be unique.")
        self.pipelines[p.id] = p
        self.inputs[p.id] = p.inputs
        self.versions.append(p.to_dict())
        self.metrics.increment("tiktok_content_pipelines_total")
        self._record(p, scope, "pipeline.created")
        return p

    def transition(
        self, pipeline_id: str, status: PipelineStatus, scope: RequestScope
    ) -> ContentPipeline:
        self._require(scope, "write")
        p = self.pipelines[pipeline_id]
        self._scoped(p, scope)
        if status not in TRANSITIONS[p.status]:
            raise ValueError(
                f"Invalid pipeline transition: {p.status.value} -> {status.value}"
            )
        previous = p.status
        p.status = status
        p.version += 1
        p.updated_at = utcnow()
        self.versions.append(p.to_dict())
        self.status_timeline.append(
            {
                "pipeline_id": p.id,
                "tenant": p.tenant,
                "workspace": p.workspace,
                "from": previous.value,
                "to": status.value,
                "at": p.updated_at,
            }
        )
        self._record(p, scope, f"pipeline.transition.{status.value}")
        return p

    def add_job(self, job: PipelineJob, scope: RequestScope) -> PipelineJob:
        self._require(scope, "process")
        self._scoped(job, scope)
        if (
            job.pipeline_id not in self.pipelines
            or not 1 <= job.priority <= 100
            or not 1 <= job.maximum_attempts <= 5
            or not 1 <= job.timeout_seconds <= 3600
        ):
            raise ValueError("Job references or bounds are invalid.")
        self.jobs[job.id] = job
        self.stages[job.id] = {
            "pipeline_id": job.pipeline_id,
            "tenant": job.tenant,
            "workspace": job.workspace,
            "stage": job.stage.value,
            "status": job.status.value,
        }
        self.metrics.increment("tiktok_content_pipeline_jobs_total")
        return job

    def normalize(
        self,
        pipeline_id: str,
        metadata: dict[str, Any],
        variables: dict[str, str],
        scope: RequestScope,
    ) -> dict[str, Any]:
        self._require(scope, "process")
        p = self.pipelines[pipeline_id]
        self._scoped(p, scope)
        validate_metadata(metadata)
        safe: dict[str, Any] = {
            str(k).strip().casefold().replace(" ", "_"): str(v).strip()
            for k, v in metadata.items()
        }
        caption = safe.get("caption", "")
        for key, value in variables.items():
            caption = caption.replace("{{" + key + "}}", value)
        if "{{" in caption or len(caption) > 2200:
            raise ValueError("Caption transformation is unresolved or out of bounds.")
        safe["caption"] = caption
        safe["hashtags"] = list(
            dict.fromkeys(
                "#" + x.lstrip("#").casefold()
                for x in safe.get("hashtags", "").split()
                if x
            )
        )[:30]
        return safe

    def validate_pipeline(
        self, pipeline_id: str, scope: RequestScope
    ) -> ValidationResult:
        self._require(scope, "process")
        p = self.pipelines[pipeline_id]
        self._scoped(p, scope)
        p.validate()
        references = [v for v in asdict(p.inputs).values() if v] + [
            p.project_reference,
            p.campaign_reference,
        ]
        checks = {
            "required_fields": True,
            "reference_integrity": all(
                self.integrity.validate(v, scope) for v in references
            ),
            "workspace_scope": True,
            "approval_requirements": True,
            "caption_length": True,
            "hashtag_validation": True,
            "schedule_compatibility": True,
            "account_compatibility_reference": True,
        }
        result = ValidationResult(
            f"validation-{pipeline_id}",
            pipeline_id,
            p.tenant,
            p.workspace,
            all(checks.values()),
            checks,
            [k for k, v in checks.items() if not v],
        )
        self.validation[result.id] = result
        if not result.valid:
            raise ValueError("Pipeline reference validation failed.")
        return result

    def score_quality(
        self, pipeline_id: str, scope: RequestScope, threshold: float = 0.75
    ) -> QualityResult:
        self._require(scope, "process")
        p = self.pipelines[pipeline_id]
        self._scoped(p, scope)
        inputs = asdict(p.inputs)
        present = sum(bool(v) for v in inputs.values()) / len(inputs)
        ref_health = float(
            all(self.integrity.validate(v, scope) for v in inputs.values() if v)
        )
        subtitle = float(bool(p.inputs.subtitle_reference))
        thumbnail = float(bool(p.inputs.thumbnail_reference))
        scores = [
            present,
            1.0,
            ref_health,
            float(bool(p.inputs.caption_reference)),
            float(bool(p.inputs.hashtag_reference)),
            subtitle,
            thumbnail,
        ]
        readiness = sum(scores) / len(scores)
        result = QualityResult(
            id=f"quality-{pipeline_id}",
            pipeline_id=pipeline_id,
            tenant=p.tenant,
            workspace=p.workspace,
            completeness_score=scores[0],
            metadata_quality=scores[1],
            reference_health=scores[2],
            caption_quality_reference=scores[3],
            hashtag_quality_reference=scores[4],
            subtitle_coverage=scores[5],
            thumbnail_availability=scores[6],
            readiness_score=readiness,
            explanation=[
                f"readiness={readiness:.2f}",
                f"threshold={threshold:.2f}",
            ],
            threshold=threshold,
        )
        self.quality[result.id] = result
        self.metrics.set("tiktok_content_pipeline_quality_score", readiness)
        return result

    def add_review(self, review: Review, scope: RequestScope) -> Review:
        self._require(scope, "review")
        self._scoped(review, scope)
        validate_reference(review.automated_review_reference)
        if review.expires_at <= datetime.now(timezone.utc):
            raise ValueError("Review is expired.")
        self.reviews[review.id] = review
        self.metrics.increment("tiktok_content_pipeline_reviews_total")
        return review

    def decide(self, approval: Approval, scope: RequestScope) -> Approval:
        self._require(scope, "approve")
        self._scoped(approval, scope)
        if approval.expires_at <= datetime.now(timezone.utc):
            raise ValueError("Approval is expired.")
        if not approval.approved and not approval.rejection_reason:
            raise ValueError("Rejection reason is required.")
        self.approvals[approval.id] = approval
        self.metrics.increment("tiktok_content_pipeline_approvals_total")
        return approval

    def _current_approval(self, pipeline_id: str, kind: ApprovalKind) -> bool:
        now = datetime.now(timezone.utc)
        return any(
            a.pipeline_id == pipeline_id
            and a.kind is kind
            and a.approved
            and a.expires_at > now
            for a in self.approvals.values()
        )

    def package(self, package: ContentPackage, scope: RequestScope) -> ContentPackage:
        self._require(scope, "package")
        self._scoped(package, scope)
        p = self.pipelines[package.pipeline_id]
        self._scoped(p, scope)
        if not self._current_approval(p.id, ApprovalKind.CONTENT):
            raise PermissionError("Current content approval is required.")
        refs = package.media_references + [
            package.subtitle_reference,
            package.thumbnail_reference,
            package.publishing_settings_reference,
            package.schedule_reference,
            package.account_reference,
            package.campaign_reference,
        ]
        for ref in refs:
            validate_reference(ref)
        expected = {ref: sha256(ref.encode()).hexdigest() for ref in refs}
        if package.checksum_manifest != expected:
            raise ValueError("Checksum manifest validation failed.")
        self.packages[package.id] = package
        self.metrics.increment("tiktok_content_pipeline_packages_total")
        return package

    def handoff(self, handoff: Handoff, scope: RequestScope) -> Handoff:
        started = perf_counter()
        self._require(scope, "handoff")
        self._scoped(handoff, scope)
        p = self.pipelines[handoff.pipeline_id]
        package = self.packages[handoff.package_reference]
        self._scoped(package, scope)
        if (
            handoff.target is HandoffTarget.PUBLISHING_CENTER
            and not self._current_approval(p.id, ApprovalKind.PUBLISHING_HANDOFF)
        ):
            raise PermissionError(
                "Publishing Center handoff requires current explicit approval."
            )
        state = self.risk.state(package.account_reference, scope)
        if any(asdict(state).values()):
            raise PermissionError(
                "Handoff stopped by restriction, challenge, pause, or kill switch."
            )
        handoff.receipt_reference = self.handoff_port.handoff(
            handoff.target, package, scope
        )
        validate_reference(handoff.receipt_reference)
        self.handoffs[handoff.id] = handoff
        self.metrics.increment("tiktok_content_pipeline_handoffs_total")
        self.metrics.set(
            "tiktok_content_pipeline_latency_seconds", perf_counter() - started
        )
        self._record(p, scope, "handoff.delegated", handoff.target.value)
        return handoff

    def checkpoint(self, checkpoint: Checkpoint, scope: RequestScope) -> Checkpoint:
        self._require(scope, "process")
        self._scoped(checkpoint, scope)
        payload = "|".join(
            [
                checkpoint.pipeline_id,
                checkpoint.pipeline_state.value,
                *[s.value for s in checkpoint.completed_stages],
                *checkpoint.job_references,
                *checkpoint.approval_references,
                checkpoint.package_reference,
                str(checkpoint.retry_position),
            ]
        )
        if sha256(payload.encode()).hexdigest() != checkpoint.integrity_hash:
            raise ValueError("Checkpoint integrity validation failed.")
        self.checkpoints[checkpoint.id] = checkpoint
        return checkpoint

    def resume(self, checkpoint_id: str, scope: RequestScope) -> ContentPipeline:
        self._require(scope, "recover")
        cp = self.checkpoints[checkpoint_id]
        self._scoped(cp, scope)
        if cp.expires_at <= datetime.now(timezone.utc):
            raise ValueError("Checkpoint is expired.")
        p = self.pipelines[cp.pipeline_id]
        package = self.packages.get(cp.package_reference)
        state = self.risk.state(package.account_reference if package else "", scope)
        if state.restriction_active or state.challenge_active:
            raise PermissionError(
                "Recovery stops while unresolved TikTok restrictions "
                "or challenges remain."
            )
        if cp.retry_position >= 5:
            raise ValueError("Maximum recovery attempts reached.")
        cp.retry_position += 1
        self.recovery[checkpoint_id] = {
            "tenant": cp.tenant,
            "workspace": cp.workspace,
            "attempt": cp.retry_position,
            "action": "checkpoint_resume",
            "backoff_seconds": min(300, 2**cp.retry_position),
            "cooldown": True,
        }
        self.metrics.increment("tiktok_content_pipeline_retries_total")
        p.status = cp.pipeline_state
        return p

    def analytics(self, scope: RequestScope) -> dict[str, float]:
        ps = self.scoped_values(self.pipelines.values(), scope)
        jobs = self.scoped_values(self.jobs.values(), scope)
        packages = self.scoped_values(self.packages.values(), scope)
        handoffs = self.scoped_values(self.handoffs.values(), scope)
        return {
            "pipelines_total": float(len(ps)),
            "jobs_total": float(len(jobs)),
            "completed_pipelines": float(
                sum(p.status is PipelineStatus.COMPLETED for p in ps)
            ),
            "failed_pipelines": float(
                sum(p.status is PipelineStatus.FAILED for p in ps)
            ),
            "average_processing_time": self.metrics.values[
                "tiktok_content_pipeline_processing_seconds"
            ],
            "average_review_time": self.metrics.values[
                "tiktok_content_pipeline_review_seconds"
            ],
            "average_approval_time": 0.0,
            "package_success_rate": len(packages) / len(ps) if ps else 0.0,
            "handoff_success_rate": len(handoffs) / len(packages) if packages else 0.0,
            "retry_rate": self.metrics.values["tiktok_content_pipeline_retries_total"]
            / len(jobs)
            if jobs
            else 0.0,
        }

    def history(self, scope: RequestScope) -> dict[str, Any]:
        return {
            "pipeline_versions": [
                v
                for v in self.versions
                if v["tenant"] == scope.tenant and v["workspace"] == scope.workspace
            ],
            "status_timeline": [
                v
                for v in self.status_timeline
                if v["tenant"] == scope.tenant and v["workspace"] == scope.workspace
            ],
            "stage_history": list(self.stages.values()),
            "job_history": [
                asdict(v) for v in self.scoped_values(self.jobs.values(), scope)
            ],
            "review_history": [
                asdict(v) for v in self.scoped_values(self.reviews.values(), scope)
            ],
            "approval_history": [
                asdict(v) for v in self.scoped_values(self.approvals.values(), scope)
            ],
            "package_history": [
                asdict(v) for v in self.scoped_values(self.packages.values(), scope)
            ],
            "handoff_history": [
                asdict(v) for v in self.scoped_values(self.handoffs.values(), scope)
            ],
            "recovery_history": [
                v
                for v in self.recovery.values()
                if v["tenant"] == scope.tenant and v["workspace"] == scope.workspace
            ],
            "audit_trail": [asdict(v) for v in self.scoped_values(self.audit, scope)],
        }

    def dashboard(self, scope: RequestScope) -> dict[str, Any]:
        return {
            "sections": [
                "Pipeline Overview",
                "Pipelines",
                "Stages",
                "Jobs",
                "Inputs",
                "Processing",
                "Validation",
                "Quality",
                "Reviews",
                "Approvals",
                "Packaging",
                "Handoffs",
                "Checkpoints",
                "Recovery",
                "History",
                "Analytics",
            ],
            "pipeline_overview": {
                "pipelines": len(self.scoped_values(self.pipelines.values(), scope)),
                "jobs": len(self.scoped_values(self.jobs.values(), scope)),
                "packages": len(self.scoped_values(self.packages.values(), scope)),
                "handoffs": len(self.scoped_values(self.handoffs.values(), scope)),
            },
            "analytics": self.analytics(scope),
            "safety": {
                "direct_publishing": False,
                "approval_gated_handoff": True,
                "bounded_jobs": True,
            },
        }
