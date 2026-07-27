import pytest

from tiktok.account_center import (
    AccountGroup,
    AccountScope,
    AccountStatus,
    AccountTag,
    BrowserBinding,
    LoginMethod,
    TikTokAccount,
    TikTokAccountCenter,
    TikTokProfile,
)


@pytest.fixture
def scope():
    return AccountScope(
        "tenant-a",
        "workspace-a",
        "operator",
        frozenset(
            {
                "tiktok:read",
                "tiktok:write",
                "tiktok:batch",
                "tiktok:login",
                "tiktok:groups",
                "tiktok:tags",
                "tiktok:risk",
            }
        ),
    )


@pytest.fixture
def center():
    return TikTokAccountCenter(encryption_key=b"x" * 32)


@pytest.fixture
def account(center, scope):
    return center.create(
        TikTokAccount(
            "acct-1",
            scope.tenant,
            scope.workspace,
            TikTokProfile(nickname="Creator", username="creator"),
            browser=BrowserBinding("browser://1"),
        ),
        scope,
    )


def test_account_crud_clone_archive_recover_batch(center, scope, account):
    clone = center.clone(account.id, scope, "acct-2")
    center.batch_status([account.id, clone.id], AccountStatus.OFFLINE, scope)
    center.archive(account.id, scope)
    center.recover(account.id, scope)
    center.delete(clone.id, scope)
    center.recover(clone.id, scope)
    assert len(center.export_accounts(scope)) == 2
    assert len(center.audit) >= 8


def test_login_encryption_expiry_and_refresh(center, scope, account):
    secret = "sessionid=plaintext-must-not-leak"
    center.login(account.id, LoginMethod.COOKIE, secret, scope)
    assert not center._state.contains_plaintext(secret)
    center.refresh_session(account.id, "refreshed-session", scope)
    with pytest.raises(PermissionError):
        center.login(account.id, LoginMethod.COOKIE, "expired", scope, valid=False)
    assert center.metrics.snapshot()["tiktok_cookie_expired_total"] == 1


def test_qr_groups_tags_search_and_dashboard(center, scope, account):
    center.add_group(
        AccountGroup(
            "g1",
            "Creators",
            scope.tenant,
            scope.workspace,
            project="launch",
            business_unit="growth",
        ),
        scope,
    )
    center.add_tag(AccountTag("t1", "priority", scope.tenant, scope.workspace), scope)
    account.group_ids.add("g1")
    account.tag_ids.add("t1")
    center.login(account.id, LoginMethod.QR, "", scope)
    assert center.search(scope, query="creator", group="g1", tag="t1") == [account]
    dashboard = center.dashboard(scope)
    assert (
        dashboard["accounts"] == 1
        and dashboard["groups"] == 1
        and dashboard["browser"] == 1
    )


def test_risk_auto_pause_and_workspace_isolation(center, scope, account):
    event = center.assess_risk(
        account.id, scope, cookie_valid=False, session_valid=False, restricted=True
    )
    assert event.score == 90 and account.auto_paused
    with pytest.raises(PermissionError):
        center.login(account.id, LoginMethod.QR, "", scope)
    other = AccountScope("tenant-a", "other", "intruder")
    assert center.search(other) == []
    with pytest.raises(PermissionError):
        center.archive(account.id, other)


def test_metrics_contract(center):
    assert set(center.metrics.snapshot()) == {
        "tiktok_accounts_total",
        "tiktok_active_accounts_total",
        "tiktok_login_success_total",
        "tiktok_login_failure_total",
        "tiktok_cookie_expired_total",
        "tiktok_session_expired_total",
        "tiktok_risk_events_total",
    }


def test_api_route_contract(center):
    from tiktok.account_center.api import ROUTES, register_tiktok_routes

    class App:
        def __init__(self):
            self.routes = []

        def add_api_route(self, path, endpoint, methods, tags):
            self.routes.append((path, tuple(methods)))

    app = App()
    register_tiktok_routes(app, center)
    paths = {path for path, _ in app.routes}
    assert set(ROUTES) <= paths
    assert {"/tiktok/dashboard", "/tiktok/metrics"} <= paths
