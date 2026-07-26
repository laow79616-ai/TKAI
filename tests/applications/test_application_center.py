from applications import ApplicationCenter, ApplicationStatus
from applications.dashboard import dashboard
from applications.sharing import can_view


def payload() -> dict[str, object]:
    return {
        "id": "support-ai",
        "name": "Support AI",
        "description": "Enterprise support",
        "version": "1.0.0",
        "owner": "alice",
        "category": "Customer Service",
        "tags": ["support"],
        "agent": "support-agent",
        "workflow": "triage",
        "plugins": ["crm"],
        "knowledge": ["support-kb"],
        "model": "enterprise-default",
        "metadata": {"organization": "acme", "teams": ["support"]},
    }


def test_application_model_catalog_lifecycle_and_versions() -> None:
    center = ApplicationCenter()
    application = center.create(payload())
    assert application.status is ApplicationStatus.DRAFT
    assert application.agent == "support-agent"
    published = center.transition(application.id, "published", "alice")
    assert published.status is ApplicationStatus.PUBLISHED
    assert center.versions.list(application.id)[0].version == "1.0.0"
    assert (
        center.transition(application.id, "running", "alice").status
        is ApplicationStatus.RUNNING
    )
    assert (
        center.transition(application.id, "paused", "alice").status
        is ApplicationStatus.PAUSED
    )


def test_templates_permissions_sharing_and_marketplace() -> None:
    center = ApplicationCenter()
    assert [item.name for item in center.templates.list()] == [
        "Assistant",
        "Customer Service",
        "Sales",
        "HR",
        "Finance",
        "Legal",
        "Operations",
        "Developer",
        "Research",
    ]
    application = center.create(payload())
    center.permissions.grant(application.id, "operator", ["view", "run"])
    assert center.permissions.check(application.id, "operator", "run")
    assert not can_view(application, principal="bob")
    center.transition(application.id, "published", "alice")
    public = center.share(application.id, "public", "alice")
    assert can_view(public, principal="bob")
    assert center.marketplace.list() == (public,)


def test_runtime_deployment_quota_audit_metrics_and_dashboard() -> None:
    center = ApplicationCenter()
    application = center.create(payload())
    deployment = center.deployments.deploy(
        application.id, application.version, "alice", replicas=2, quota=1
    )
    result = center.runtime.execute(deployment, {"message": "hello"}, "alice")
    center.deployments.record_run(deployment.id)
    assert result["status"] == "completed"
    assert center.metrics.snapshot() == {
        "applications_total": 1,
        "deployments_total": 1,
        "application_runs_total": 1,
        "application_failures_total": 0,
    }
    assert dashboard(center)["deployments"] == 1
    assert "application_runs_total 1" in center.metrics.render_prometheus()
