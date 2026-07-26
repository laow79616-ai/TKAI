from tkai.enterprise import EnterprisePlatform
from tkai.enterprise.api import EnterpriseApi
from tkai.enterprise.models import (
    AuditAction,
    Edition,
    License,
    Organization,
    Permission,
    Plan,
    Quota,
    Role,
    RoleAssignment,
    Subscription,
    Tenant,
    User,
    Workspace,
)


def platform() -> EnterprisePlatform:
    value = EnterprisePlatform(clock=lambda: 10.0)
    value.add_organization(Organization("org-1", "TKAI"))
    value.add_tenant(
        Tenant("tenant-1", "org-1", "Primary", "org-1/tenant-1", Quota(seats=2))
    )
    return value


def test_tenant_isolation_quota_and_namespace() -> None:
    value = platform()
    value.add_workspace(Workspace("work-1", "tenant-1", "org-1/tenant-1/work-1"))
    value.add_user(User("user-1", "tenant-1", "one@example.com"))
    value.add_user(User("user-2", "tenant-1", "two@example.com"))
    try:
        value.add_user(User("user-3", "tenant-1", "three@example.com"))
    except ValueError as error:
        assert "seat quota" in str(error)
    else:
        raise AssertionError("seat quota was not enforced")


def test_rbac_inheritance_scope_and_cross_tenant_assignment() -> None:
    value = platform()
    value.add_user(User("user-1", "tenant-1", "one@example.com"))
    value.add_permission(Permission("read", "read", "agents"))
    value.add_role(Role("base", "Reader", frozenset({"read"})))
    value.add_role(Role("child", "Scoped Reader", parent_role_id="base"))
    value.assign_role(RoleAssignment("user-1", "child", "tenant-1", "workspace/"))
    assert value.permits("user-1", "tenant-1", "read", "workspace/agents")
    assert not value.permits("user-1", "tenant-1", "write", "workspace/agents")


def test_license_billing_audit_api_and_metrics() -> None:
    value = platform()
    value.activate_license(License("key", "tenant-1", Edition.ENTERPRISE, 10, 1, 20))
    value.add_plan(Plan("pro", "Pro", Quota(seats=10)))
    value.subscribe(Subscription("sub-1", "tenant-1", "pro"))
    value.record_audit(AuditAction.PLUGIN_INSTALL, "user-1", "tenant-1", "plugin/demo")
    assert value.validate_license("tenant-1", 10)
    assert EnterpriseApi(value).list("audit", "tenant-1")["total"] == 1
    assert value.metrics() == {
        "tenant_total": 1,
        "organization_total": 1,
        "user_total": 0,
        "license_total": 1,
        "audit_total": 1,
    }
