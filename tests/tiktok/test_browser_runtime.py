from pathlib import Path

import pytest

from tiktok.browser_runtime import (
    BrowserEngine,
    BrowserInstance,
    BrowserProfile,
    BrowserStatus,
    FingerprintConfiguration,
    HealthSnapshot,
    RuntimeScope,
    TikTokBrowserRuntime,
)


@pytest.fixture
def scope():
    return RuntimeScope(
        "tenant-a",
        "workspace-a",
        "operator",
        frozenset(
            {
                "tiktok:browser:read",
                "tiktok:browser:write",
                "tiktok:browser:launch",
                "tiktok:browser:control",
                "tiktok:browser:navigate",
                "tiktok:browser:storage",
                "tiktok:browser:session",
                "tiktok:browser:health",
                "tiktok:browser:recover",
                "tiktok:browser:admin",
            }
        ),
    )


@pytest.fixture
def runtime(tmp_path):
    return TikTokBrowserRuntime(
        encryption_key=b"x" * 32,
        profile_root=tmp_path,
        maximum_pool_size=2,
        per_account_limit=1,
        maximum_tabs=2,
    )


@pytest.fixture
def instance(runtime, scope):
    runtime.create_profile(
        BrowserProfile(
            "profile-1",
            scope.tenant,
            scope.workspace,
            account_reference="account-1",
            profile_directory_reference="profiles/account-1",
        ),
        scope,
    )
    return runtime.create_instance(
        BrowserInstance(
            "browser-1",
            "Primary",
            "account-1",
            scope.tenant,
            scope.workspace,
            scope.actor,
            BrowserEngine.CHROMIUM,
            profile_reference="profile-1",
        ),
        scope,
    )


def test_lifecycle_context_pages_and_pool(runtime, scope, instance):
    runtime.launch(instance.id, scope)
    context = runtime.create_context(instance.id, scope, persistent=True)
    runtime.context_action(context.id, "launch", scope)
    page = runtime.create_page(context.id, scope)
    runtime.navigate(page.id, "https://www.tiktok.com/", scope)
    runtime.navigate(page.id, "https://www.tiktok.com/login", scope)
    assert runtime.page_action(page.id, "back", scope).url.endswith("tiktok.com/")
    runtime.create_page(context.id, scope)
    with pytest.raises(RuntimeError):
        runtime.create_page(context.id, scope)
    assert runtime.release(instance.id, scope).status is BrowserStatus.IDLE
    runtime.acquire(scope, "account-1")
    runtime.pause(instance.id, scope)
    runtime.resume(instance.id, scope)
    assert runtime.stop(instance.id, scope).status is BrowserStatus.STOPPED


def test_profile_fingerprint_path_and_scope_security(runtime, scope):
    with pytest.raises(ValueError):
        runtime.create_profile(
            BrowserProfile(
                "bad",
                scope.tenant,
                scope.workspace,
                profile_directory_reference="../escape",
            ),
            scope,
        )
    with pytest.raises(ValueError):
        FingerprintConfiguration(touch_support=True).validate()
    outside = str(Path(scope.workspace).resolve())
    with pytest.raises(ValueError):
        runtime.create_profile(
            BrowserProfile(
                "absolute",
                scope.tenant,
                scope.workspace,
                profile_directory_reference=outside,
            ),
            scope,
        )


def test_encrypted_storage_session_and_account_integration(runtime, scope, instance):
    runtime.launch(instance.id, scope)
    context = runtime.create_context(instance.id, scope)
    secret = "sessionid=must-not-be-plaintext"
    runtime.save_storage(context.id, {"cookies": [secret]}, scope)
    assert not runtime.storage.contains_plaintext(secret)
    assert runtime.restore_storage(context.id, scope)["cookies"] == [secret]
    assert (
        runtime.validate_tiktok_session(
            instance.id, "https://www.tiktok.com/", scope, logged_in=True
        )
        == "logged_in"
    )
    with pytest.raises(ValueError):
        runtime.validate_tiktok_session(
            instance.id, "https://example.com/", scope, logged_in=True
        )


def test_scheduling_concurrency_cancellation_and_kill_switch(runtime, scope, instance):
    second = runtime.create_instance(
        BrowserInstance(
            "browser-2",
            "Second",
            "account-2",
            scope.tenant,
            scope.workspace,
            scope.actor,
        ),
        scope,
    )
    cancelled = runtime.enqueue(instance.id, scope, priority=1)
    runtime.cancel(cancelled.id, scope)
    runtime.enqueue(second.id, scope, priority=2)
    assert runtime.schedule_next(scope) is second
    runtime.launch(instance.id, scope)
    runtime.set_kill_switch(True, scope)
    assert instance.status is BrowserStatus.STOPPED
    with pytest.raises(RuntimeError):
        runtime.launch(instance.id, scope)


def test_health_recovery_dashboard_metrics_and_isolation(runtime, scope, instance):
    runtime.launch(instance.id, scope)
    runtime.record_health(
        HealthSnapshot(
            instance.id,
            "healthy",
            "healthy",
            "healthy",
            "reachable",
            "logged_in",
            "healthy",
            1024,
            "cpu://browser-1",
        ),
        scope,
    )
    record = runtime.recover(instance.id, scope, "mock crash")
    assert record.recovered
    dashboard = runtime.dashboard(scope)
    assert dashboard["instances"] == 1
    assert dashboard["health"] == 1
    assert (
        runtime.metrics.snapshot()["tiktok_browser_crashes_total"] == 1
        and runtime.metrics.snapshot()["tiktok_browser_recoveries_total"] == 1
    )
    other = RuntimeScope("tenant-a", "other", "intruder")
    assert runtime.list_instances(other) == []
    with pytest.raises(PermissionError):
        runtime.stop(instance.id, other)


def test_api_route_contract(runtime):
    from tiktok.browser_runtime.api import ROUTES, register_browser_runtime_routes

    class App:
        def __init__(self):
            self.routes = []

        def add_api_route(self, path, endpoint, methods, tags):
            self.routes.append((path, tuple(methods)))

    app = App()
    register_browser_runtime_routes(app, runtime)
    paths = {path for path, _ in app.routes}
    assert set(ROUTES) <= paths
    assert {
        "/tiktok/browser-runtime/dashboard",
        "/tiktok/browser-runtime/metrics",
    } <= paths
