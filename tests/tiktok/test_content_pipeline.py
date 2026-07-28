"""Offline coverage for the Enterprise TikTok Content Pipeline."""

from datetime import timedelta
from hashlib import sha256

import pytest

from tiktok.content_pipeline import (
    Approval,
    ApprovalKind,
    Checkpoint,
    ContentPackage,
    ContentPipeline,
    Handoff,
    HandoffTarget,
    JobKind,
    PipelineInput,
    PipelineJob,
    PipelineStatus,
    RequestScope,
    Review,
    ReviewStatus,
    StageKind,
    TikTokContentPipeline,
)
from tiktok.content_pipeline.adapters import BoundedTestDouble
from tiktok.content_pipeline.api import ROUTES
from tiktok.content_pipeline.metrics import METRIC_NAMES
from tiktok.content_pipeline.models import utcnow


def scope(workspace: str = "workspace") -> RequestScope:
    return RequestScope(
        "tenant", workspace, "operator", frozenset({"tiktok:content-pipeline:admin"})
    )


def pipeline() -> ContentPipeline:
    return ContentPipeline(
        "pipe-1",
        "Launch content",
        "Bounded content preparation",
        "tenant",
        "workspace",
        "owner",
        "ref://project/1",
        "campaign://1",
        inputs=PipelineInput(
            video_reference="encrypted://video/1",
            caption_reference="content://caption/1",
            hashtag_reference="content://hashtags/1",
            subtitle_reference="content://subtitles/1",
            thumbnail_reference="content://thumbnail/1",
        ),
    )


def package() -> ContentPackage:
    refs = [
        "encrypted://video/1",
        "content://subtitles/1",
        "content://thumbnail/1",
        "ref://publishing-settings/1",
        "schedule://1",
        "account://1",
        "campaign://1",
    ]
    return ContentPackage(
        "package-1",
        "pipe-1",
        "tenant",
        "workspace",
        refs[:1],
        "Caption",
        ["#safe"],
        *refs[1:],
        1,
        {r: sha256(r.encode()).hexdigest() for r in refs},
    )


def ready() -> tuple[TikTokContentPipeline, BoundedTestDouble]:
    adapter = BoundedTestDouble()
    center = TikTokContentPipeline(adapter, adapter, adapter)
    center.create_pipeline(pipeline(), scope())
    return center, adapter


def approve(center: TikTokContentPipeline, kind: ApprovalKind) -> None:
    center.decide(
        Approval(
            f"approval-{kind.value}",
            "pipe-1",
            "tenant",
            "workspace",
            kind,
            "reviewer",
            True,
            "approved",
            utcnow() + timedelta(hours=1),
        ),
        scope(),
    )


def test_crud_lifecycle_inputs_jobs_transformations_validation_and_quality() -> None:
    center, _ = ready()
    assert center.transition("pipe-1", PipelineStatus.CONFIGURED, scope()).version == 2
    center.transition("pipe-1", PipelineStatus.VALIDATING, scope())
    assert center.validate_pipeline("pipe-1", scope()).valid
    quality = center.score_quality("pipe-1", scope())
    assert 0 <= quality.readiness_score <= 1 and quality.explanation
    job = center.add_job(
        PipelineJob(
            "job-1",
            "pipe-1",
            "tenant",
            "workspace",
            JobKind.TRANSFORMATION,
            StageKind.TRANSFORMATION,
        ),
        scope(),
    )
    assert job.maximum_attempts == 3
    transformed = center.normalize(
        "pipe-1",
        {"Caption": "Hello {{name}}", "Hashtags": "One #TWO one"},
        {"name": "TikTok"},
        scope(),
    )
    assert transformed == {"caption": "Hello TikTok", "hashtags": ["#one", "#two"]}
    with pytest.raises(ValueError, match="unresolved"):
        center.normalize("pipe-1", {"caption": "{{code}}"}, {}, scope())


def test_reference_checksum_security_isolation_and_rbac() -> None:
    center, _ = ready()
    invalid = pipeline()
    invalid.id = "bad"
    invalid.inputs.video_reference = "C:\\plain\\video.mp4"
    with pytest.raises(ValueError, match="encrypted"):
        center.create_pipeline(invalid, scope())
    unsafe = pipeline()
    unsafe.id = "secret"
    unsafe.metadata = {"cookie": "plain"}
    with pytest.raises(ValueError, match="Secrets"):
        center.create_pipeline(unsafe, scope())
    with pytest.raises(PermissionError, match="Cross-tenant"):
        center.create_pipeline(pipeline(), scope("other"))
    with pytest.raises(PermissionError, match="write"):
        TikTokContentPipeline().create_pipeline(
            pipeline(), RequestScope("tenant", "workspace", "reader")
        )
    approve(center, ApprovalKind.CONTENT)
    broken = package()
    broken.checksum_manifest = {}
    with pytest.raises(ValueError, match="Checksum"):
        center.package(broken, scope())


def test_reviews_approval_packaging_and_publishing_handoff_enforcement() -> None:
    center, adapter = ready()
    center.add_review(
        Review(
            "review-1",
            "pipe-1",
            "tenant",
            "workspace",
            "human",
            ReviewStatus.APPROVED,
            "ready",
            [],
            "ref://automated-review/1",
            utcnow() + timedelta(hours=1),
        ),
        scope(),
    )
    with pytest.raises(PermissionError, match="content approval"):
        center.package(package(), scope())
    approve(center, ApprovalKind.CONTENT)
    center.package(package(), scope())
    handoff = Handoff(
        "handoff-1",
        "pipe-1",
        "package-1",
        "tenant",
        "workspace",
        HandoffTarget.PUBLISHING_CENTER,
    )
    with pytest.raises(PermissionError, match="explicit approval"):
        center.handoff(handoff, scope())
    assert adapter.handoffs == []
    approve(center, ApprovalKind.PUBLISHING_HANDOFF)
    result = center.handoff(handoff, scope())
    assert result.receipt_reference.startswith("ref://publishing_center/receipt/")
    assert adapter.handoffs == [(HandoffTarget.PUBLISHING_CENTER, "package-1")]


@pytest.mark.parametrize(
    "target",
    [
        HandoffTarget.CREATOR_WORKSPACE,
        HandoffTarget.CAMPAIGN_CENTER,
        HandoffTarget.CONTENT_CENTER,
        HandoffTarget.WORKFLOW_CENTER,
        HandoffTarget.AUTOMATION_ENGINE,
        HandoffTarget.TASK_SCHEDULER,
        HandoffTarget.EXECUTION_ENGINE,
    ],
)
def test_bounded_integration_handoffs(target: HandoffTarget) -> None:
    center, adapter = ready()
    approve(center, ApprovalKind.CONTENT)
    center.package(package(), scope())
    center.handoff(
        Handoff(
            f"h-{target.value}", "pipe-1", "package-1", "tenant", "workspace", target
        ),
        scope(),
    )
    assert adapter.handoffs[-1][0] is target


def test_checkpoint_integrity_recovery_bounds_and_restriction_challenge_stop() -> None:
    center, adapter = ready()
    approve(center, ApprovalKind.CONTENT)
    center.package(package(), scope())
    payload = "|".join(
        [
            "pipe-1",
            PipelineStatus.PACKAGED.value,
            "intake",
            "job-1",
            "approval-content",
            "package-1",
            "0",
        ]
    )
    cp = Checkpoint(
        "cp-1",
        "pipe-1",
        "tenant",
        "workspace",
        PipelineStatus.PACKAGED,
        [StageKind.INTAKE],
        list(StageKind)[1:],
        ["job-1"],
        ["approval-content"],
        "package-1",
        0,
        sha256(payload.encode()).hexdigest(),
        utcnow() + timedelta(hours=1),
    )
    center.checkpoint(cp, scope())
    assert center.resume("cp-1", scope()).status is PipelineStatus.PACKAGED
    adapter.safety.restriction_active = True
    with pytest.raises(PermissionError, match="restrictions"):
        center.resume("cp-1", scope())
    adapter.safety.restriction_active = False
    adapter.safety.challenge_active = True
    with pytest.raises(PermissionError, match="challenges"):
        center.resume("cp-1", scope())
    bad = cp
    bad.id = "cp-bad"
    bad.integrity_hash = "bad"
    with pytest.raises(ValueError, match="integrity"):
        center.checkpoint(bad, scope())


def test_api_dashboard_history_analytics_metrics_and_no_direct_publish() -> None:
    center, _ = ready()
    assert len(ROUTES) == 14 and len(center.dashboard(scope())["sections"]) == 16
    assert center.dashboard(scope())["safety"]["direct_publishing"] is False
    assert center.history(scope())["pipeline_versions"]
    assert center.analytics(scope())["pipelines_total"] == 1
    assert all(name in center.metrics.render_prometheus() for name in METRIC_NAMES)
    assert not hasattr(center, "publish")
