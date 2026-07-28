"""Enterprise TikTok browser runtime with bounded local reference behavior."""

from __future__ import annotations

import heapq
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from typing import Any
from uuid import uuid4

from .adapters import (
    AccountStatusPort,
    BrowserDriver,
    NullAccountStatusPort,
    ReferenceBrowserDriver,
    sanitized_metadata,
)
from .metrics import BrowserRuntimeMetrics
from .models import (
    BrowserContext,
    BrowserInstance,
    BrowserPage,
    BrowserProfile,
    BrowserStatus,
    HealthSnapshot,
    LaunchRequest,
    RecoveryRecord,
    RuntimeScope,
)
from .security import EncryptedStorageState, validate_directory_reference


class TikTokBrowserRuntime:
    """Tenant-isolated orchestration layer; browser execution is adapter-driven."""

    def __init__(
        self,
        *,
        driver: BrowserDriver | None = None,
        account_status: AccountStatusPort | None = None,
        encryption_key: bytes | None = None,
        profile_root: Path | None = None,
        minimum_pool_size: int = 0,
        maximum_pool_size: int = 20,
        per_account_limit: int = 1,
        per_workspace_limit: int = 10,
        maximum_tabs: int = 8,
        navigation_timeout_seconds: int = 30,
        maximum_recovery_attempts: int = 3,
    ) -> None:
        bounds = (
            maximum_pool_size,
            per_account_limit,
            per_workspace_limit,
            maximum_tabs,
            navigation_timeout_seconds,
            maximum_recovery_attempts,
        )
        if minimum_pool_size < 0 or any(value < 1 for value in bounds):
            raise ValueError("Runtime resource bounds must be positive.")
        if minimum_pool_size > maximum_pool_size:
            raise ValueError("Minimum pool size cannot exceed maximum pool size.")
        self.driver = driver or ReferenceBrowserDriver()
        self.account_status = account_status or NullAccountStatusPort()
        self.storage = EncryptedStorageState(encryption_key)
        self.profile_root = profile_root
        self.minimum_pool_size = minimum_pool_size
        self.maximum_pool_size = maximum_pool_size
        self.per_account_limit = per_account_limit
        self.per_workspace_limit = per_workspace_limit
        self.maximum_tabs = maximum_tabs
        self.navigation_timeout_seconds = navigation_timeout_seconds
        self.maximum_recovery_attempts = maximum_recovery_attempts
        self.instances: dict[str, BrowserInstance] = {}
        self.profiles: dict[str, BrowserProfile] = {}
        self.contexts: dict[str, BrowserContext] = {}
        self.pages: dict[str, BrowserPage] = {}
        self.health_records: dict[str, HealthSnapshot] = {}
        self.recoveries: list[RecoveryRecord] = []
        self.audit: list[dict[str, str]] = []
        self._queue: list[LaunchRequest] = []
        self._cancelled_requests: set[str] = set()
        self.metrics = BrowserRuntimeMetrics()
        self.kill_switch = False

    @staticmethod
    def _require(scope: RuntimeScope, action: str) -> None:
        required = f"tiktok:browser:{action}"
        if (
            required not in scope.permissions
            and "tiktok:browser:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    @staticmethod
    def _scoped(item: Any, scope: RuntimeScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-workspace browser runtime access denied.")

    def _audit(self, action: str, resource: str, scope: RuntimeScope) -> None:
        self.audit.append(
            {
                "action": action,
                "resource": resource,
                "actor": scope.actor,
                "tenant": scope.tenant,
                "workspace": scope.workspace,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def _instance(self, instance_id: str, scope: RuntimeScope) -> BrowserInstance:
        instance = self.instances[instance_id]
        self._scoped(instance, scope)
        return instance

    def _context(self, context_id: str, scope: RuntimeScope) -> BrowserContext:
        context = self.contexts[context_id]
        self._scoped(context, scope)
        return context

    def _page(self, page_id: str, scope: RuntimeScope) -> BrowserPage:
        page = self.pages[page_id]
        self._scoped(page, scope)
        return page

    def _active_instances(self) -> list[BrowserInstance]:
        return [
            item
            for item in self.instances.values()
            if item.status
            in {BrowserStatus.RUNNING, BrowserStatus.IDLE, BrowserStatus.PAUSED}
        ]

    def _update_metrics(self) -> None:
        self.metrics.set("tiktok_browser_active_total", len(self._active_instances()))
        self.metrics.set("tiktok_browser_contexts_total", len(self.contexts))
        self.metrics.set("tiktok_browser_pages_total", len(self.pages))
        self.metrics.set("tiktok_browser_queue_depth", len(self._queue))
        self.metrics.set(
            "tiktok_browser_memory_bytes",
            sum(item.memory_bytes for item in self.health_records.values()),
        )

    def create_profile(
        self, profile: BrowserProfile, scope: RuntimeScope
    ) -> BrowserProfile:
        self._require(scope, "write")
        self._scoped(profile, scope)
        if not profile.id or profile.id in self.profiles:
            raise ValueError("Profile ID must be non-empty and unique.")
        validate_directory_reference(
            profile.profile_directory_reference, self.profile_root
        )
        validate_directory_reference(
            profile.download_directory_reference, self.profile_root
        )
        profile.fingerprint.validate()
        if min(*profile.viewport, *profile.screen_resolution) < 1:
            raise ValueError("Viewport and screen dimensions must be positive.")
        self.profiles[profile.id] = profile
        self._audit("profile.create", profile.id, scope)
        return profile

    def create_instance(
        self, instance: BrowserInstance, scope: RuntimeScope
    ) -> BrowserInstance:
        self._require(scope, "write")
        self._scoped(instance, scope)
        if not instance.id or instance.id in self.instances:
            raise ValueError("Browser instance ID must be non-empty and unique.")
        if instance.profile_reference:
            profile = self.profiles[instance.profile_reference]
            self._scoped(profile, scope)
            if profile.account_reference and (
                profile.account_reference != instance.account_reference
            ):
                raise PermissionError(
                    "Profile account binding does not match instance."
                )
        instance.metadata = sanitized_metadata(instance.metadata)
        self.instances[instance.id] = instance
        self.metrics.increment("tiktok_browser_instances_total")
        self._audit("instance.create", instance.id, scope)
        return instance

    def launch(self, instance_id: str, scope: RuntimeScope) -> BrowserInstance:
        self._require(scope, "launch")
        if self.kill_switch:
            raise RuntimeError("Browser runtime kill switch is active.")
        instance = self._instance(instance_id, scope)
        active = self._active_instances()
        if len(active) >= self.maximum_pool_size:
            raise RuntimeError("Browser pool maximum reached.")
        if (
            sum(i.account_reference == instance.account_reference for i in active)
            >= self.per_account_limit
        ):
            raise RuntimeError("Per-account browser limit reached.")
        if (
            sum(
                i.tenant == scope.tenant and i.workspace == scope.workspace
                for i in active
            )
            >= self.per_workspace_limit
        ):
            raise RuntimeError("Per-workspace browser limit reached.")
        started = monotonic()
        instance.status = BrowserStatus.PROVISIONING
        try:
            instance.process_id_reference = self.driver.launch(instance)
            instance.status = BrowserStatus.RUNNING
            instance.last_active_at = datetime.now(timezone.utc)
            self.metrics.increment("tiktok_browser_launch_total")
            self.metrics.set(
                "tiktok_browser_launch_latency_seconds", monotonic() - started
            )
        except Exception as error:
            instance.status = BrowserStatus.FAILED
            self.metrics.increment("tiktok_browser_launch_failures_total")
            raise RuntimeError("Browser driver launch failed.") from error
        self._update_metrics()
        self._audit("instance.launch", instance.id, scope)
        return instance

    def pause(self, instance_id: str, scope: RuntimeScope) -> BrowserInstance:
        self._require(scope, "control")
        instance = self._instance(instance_id, scope)
        if instance.status not in {BrowserStatus.RUNNING, BrowserStatus.IDLE}:
            raise ValueError("Only running or idle browsers can be paused.")
        instance.status = BrowserStatus.PAUSED
        self._audit("instance.pause", instance.id, scope)
        return instance

    def resume(self, instance_id: str, scope: RuntimeScope) -> BrowserInstance:
        self._require(scope, "control")
        instance = self._instance(instance_id, scope)
        if instance.status is not BrowserStatus.PAUSED:
            raise ValueError("Only paused browsers can be resumed.")
        instance.status = BrowserStatus.RUNNING
        instance.last_active_at = datetime.now(timezone.utc)
        self._audit("instance.resume", instance.id, scope)
        return instance

    def stop(self, instance_id: str, scope: RuntimeScope) -> BrowserInstance:
        self._require(scope, "control")
        instance = self._instance(instance_id, scope)
        if instance.process_id_reference:
            self.driver.stop(instance.process_id_reference)
        instance.process_id_reference = ""
        instance.status = BrowserStatus.STOPPED
        for context in self.contexts.values():
            if context.instance_id == instance.id:
                context.status = "closed"
        self._update_metrics()
        self._audit("instance.stop", instance.id, scope)
        return instance

    def set_kill_switch(self, enabled: bool, scope: RuntimeScope) -> None:
        self._require(scope, "admin")
        self.kill_switch = enabled
        if enabled:
            for instance in list(self.instances.values()):
                if (
                    instance.tenant == scope.tenant
                    and instance.workspace == scope.workspace
                    and instance.status
                    in {BrowserStatus.RUNNING, BrowserStatus.IDLE, BrowserStatus.PAUSED}
                ):
                    self.stop(instance.id, scope)
        self._audit("runtime.kill_switch", str(enabled).lower(), scope)

    def create_context(
        self,
        instance_id: str,
        scope: RuntimeScope,
        *,
        persistent: bool = False,
        maximum_lifetime_seconds: int = 3600,
        idle_timeout_seconds: int = 300,
    ) -> BrowserContext:
        self._require(scope, "control")
        instance = self._instance(instance_id, scope)
        if instance.status not in {BrowserStatus.RUNNING, BrowserStatus.IDLE}:
            raise ValueError("Browser must be running to create a context.")
        if maximum_lifetime_seconds < 1 or idle_timeout_seconds < 1:
            raise ValueError("Context timeouts must be positive.")
        context_id = str(uuid4())
        context = BrowserContext(
            context_id,
            instance.id,
            scope.tenant,
            scope.workspace,
            persistent=persistent,
            storage_reference=f"storage://{scope.tenant}/{scope.workspace}/{context_id}",
            maximum_lifetime_seconds=maximum_lifetime_seconds,
            idle_timeout_seconds=idle_timeout_seconds,
        )
        self.contexts[context.id] = context
        self._update_metrics()
        self._audit("context.create", context.id, scope)
        return context

    def context_action(
        self, context_id: str, action: str, scope: RuntimeScope
    ) -> BrowserContext:
        self._require(scope, "control")
        context = self._context(context_id, scope)
        transitions = {
            "launch": ({"created", "restored"}, "running"),
            "pause": ({"running"}, "paused"),
            "resume": ({"paused"}, "running"),
            "close": ({"created", "running", "paused", "restored"}, "closed"),
            "recycle": ({"closed", "failed"}, "created"),
            "restore": ({"closed", "failed"}, "restored"),
        }
        if action not in transitions:
            raise ValueError("Unsupported context action.")
        expected, target = transitions[action]
        if context.status not in expected:
            raise ValueError(f"Context cannot {action} from {context.status}.")
        context.status = target
        context.last_active_at = datetime.now(timezone.utc)
        self._audit(f"context.{action}", context.id, scope)
        return context

    def create_page(self, context_id: str, scope: RuntimeScope) -> BrowserPage:
        self._require(scope, "control")
        context = self._context(context_id, scope)
        if context.status != "running":
            raise ValueError("Context must be running to create a tab.")
        existing = [
            page for page in self.pages.values() if page.context_id == context.id
        ]
        if len(existing) >= self.maximum_tabs:
            raise RuntimeError("Maximum tabs per browser reached.")
        for page in existing:
            page.active = False
        page = BrowserPage(str(uuid4()), context.id, scope.tenant, scope.workspace)
        self.pages[page.id] = page
        self._update_metrics()
        self._audit("page.create", page.id, scope)
        return page

    def close_page(self, page_id: str, scope: RuntimeScope) -> None:
        self._require(scope, "control")
        page = self._page(page_id, scope)
        del self.pages[page.id]
        self._update_metrics()
        self._audit("page.close", page.id, scope)

    def navigate(
        self,
        page_id: str,
        url: str,
        scope: RuntimeScope,
        *,
        timeout_seconds: int | None = None,
    ) -> BrowserPage:
        self._require(scope, "navigate")
        page = self._page(page_id, scope)
        timeout = timeout_seconds or self.navigation_timeout_seconds
        if timeout < 1 or timeout > self.navigation_timeout_seconds:
            raise ValueError("Navigation timeout exceeds the configured bound.")
        if not url.startswith(("https://", "http://", "about:")):
            raise ValueError("Navigation URL must use HTTP, HTTPS, or about.")
        page.navigation_history = page.navigation_history[: page.history_index + 1]
        page.navigation_history.append(url)
        page.history_index += 1
        page.url = url
        self._audit("page.navigate", page.id, scope)
        return page

    def page_action(
        self, page_id: str, action: str, scope: RuntimeScope
    ) -> BrowserPage:
        self._require(scope, "navigate")
        page = self._page(page_id, scope)
        if action == "reload" or action == "wait_for_load":
            return page
        delta = -1 if action == "back" else 1 if action == "forward" else 0
        target = page.history_index + delta
        if delta == 0 or target < 0 or target >= len(page.navigation_history):
            raise ValueError("Page history action is unavailable.")
        page.history_index = target
        page.url = page.navigation_history[target]
        return page

    def save_storage(
        self, context_id: str, state: dict[str, Any], scope: RuntimeScope
    ) -> str:
        self._require(scope, "storage")
        context = self._context(context_id, scope)
        reference = context.storage_reference
        self.storage.export(reference, state)
        self._audit("storage.export", context.id, scope)
        return reference

    def restore_storage(self, context_id: str, scope: RuntimeScope) -> dict[str, Any]:
        self._require(scope, "storage")
        context = self._context(context_id, scope)
        self._audit("storage.import", context.id, scope)
        return self.storage.import_state(context.storage_reference)

    def validate_tiktok_session(
        self, instance_id: str, url: str, scope: RuntimeScope, *, logged_in: bool
    ) -> str:
        self._require(scope, "session")
        instance = self._instance(instance_id, scope)
        if "tiktok.com" not in url.casefold():
            raise ValueError("Session validation is restricted to TikTok domains.")
        login_page = "/login" in url.casefold()
        expired = login_page or not logged_in
        risk = "session_expired" if expired else "none"
        self.account_status.update_login_status(
            instance.account_reference,
            scope.tenant,
            scope.workspace,
            logged_in=logged_in and not login_page,
            expired=expired,
            risk=risk,
        )
        self._audit("session.validate", instance.id, scope)
        return "expired" if expired else "logged_in"

    def enqueue(
        self,
        instance_id: str,
        scope: RuntimeScope,
        *,
        priority: int = 0,
        timeout_seconds: int = 30,
    ) -> LaunchRequest:
        self._require(scope, "launch")
        instance = self._instance(instance_id, scope)
        if len(self._queue) >= self.maximum_pool_size * 4:
            raise RuntimeError("Launch queue backpressure limit reached.")
        request = LaunchRequest(
            (-priority, datetime.now(timezone.utc)),
            str(uuid4()),
            instance.id,
            scope.tenant,
            scope.workspace,
            instance.account_reference,
            priority,
            timeout_seconds,
        )
        heapq.heappush(self._queue, request)
        self._update_metrics()
        self._audit("queue.enqueue", request.id, scope)
        return request

    def cancel(self, request_id: str, scope: RuntimeScope) -> None:
        self._require(scope, "launch")
        request = next(item for item in self._queue if item.id == request_id)
        self._scoped(request, scope)
        request.cancelled = True
        self._cancelled_requests.add(request.id)
        self._audit("queue.cancel", request.id, scope)

    def schedule_next(self, scope: RuntimeScope) -> BrowserInstance | None:
        self._require(scope, "launch")
        deferred: list[LaunchRequest] = []
        selected: LaunchRequest | None = None
        while self._queue:
            request = heapq.heappop(self._queue)
            if request.cancelled:
                continue
            if request.tenant == scope.tenant and request.workspace == scope.workspace:
                selected = request
                break
            deferred.append(request)
        for request in deferred:
            heapq.heappush(self._queue, request)
        self._update_metrics()
        return self.launch(selected.instance_id, scope) if selected else None

    def acquire(
        self, scope: RuntimeScope, account_reference: str = ""
    ) -> BrowserInstance:
        self._require(scope, "control")
        candidates = [
            instance
            for instance in self.instances.values()
            if instance.tenant == scope.tenant
            and instance.workspace == scope.workspace
            and instance.status in {BrowserStatus.READY, BrowserStatus.IDLE}
            and (
                not account_reference or instance.account_reference == account_reference
            )
        ]
        if not candidates:
            raise RuntimeError("No browser instance is available.")
        instance = candidates[0]
        return (
            self.launch(instance.id, scope)
            if instance.status is BrowserStatus.READY
            else self.resume(instance.id, scope)
            if instance.status is BrowserStatus.PAUSED
            else instance
        )

    def release(self, instance_id: str, scope: RuntimeScope) -> BrowserInstance:
        self._require(scope, "control")
        instance = self._instance(instance_id, scope)
        if instance.status is not BrowserStatus.RUNNING:
            raise ValueError("Only running browser instances can be released.")
        instance.status = BrowserStatus.IDLE
        self._update_metrics()
        self._audit("pool.release", instance.id, scope)
        return instance

    def drain(self, scope: RuntimeScope) -> int:
        self._require(scope, "admin")
        count = 0
        for instance in list(self.instances.values()):
            if (
                instance.tenant == scope.tenant
                and instance.workspace == scope.workspace
                and instance.status
                not in {BrowserStatus.STOPPED, BrowserStatus.DELETED}
            ):
                self.stop(instance.id, scope)
                count += 1
        self._audit("pool.drain", str(count), scope)
        return count

    def record_health(
        self, snapshot: HealthSnapshot, scope: RuntimeScope
    ) -> HealthSnapshot:
        self._require(scope, "health")
        self._instance(snapshot.instance_id, scope)
        self.health_records[snapshot.instance_id] = snapshot
        self._update_metrics()
        return snapshot

    def recover(
        self, instance_id: str, scope: RuntimeScope, reason: str
    ) -> RecoveryRecord:
        self._require(scope, "recover")
        instance = self._instance(instance_id, scope)
        instance.status = BrowserStatus.RECOVERING
        self.metrics.increment("tiktok_browser_crashes_total")
        record = RecoveryRecord(
            instance.id, 0, self.maximum_recovery_attempts, 1.0, reason
        )
        self.recoveries.append(record)
        for attempt in range(1, self.maximum_recovery_attempts + 1):
            record.attempts = attempt
            try:
                if instance.process_id_reference:
                    self.driver.stop(instance.process_id_reference)
                instance.process_id_reference = self.driver.launch(instance)
                instance.status = BrowserStatus.RUNNING
                record.recovered = True
                self.metrics.increment("tiktok_browser_recoveries_total")
                break
            except Exception:
                record.backoff_seconds *= 2
        if not record.recovered:
            instance.status = BrowserStatus.FAILED
            self.account_status.auto_pause(
                instance.account_reference, scope.tenant, scope.workspace, reason
            )
        self._audit("instance.recover", instance.id, scope)
        self._update_metrics()
        return record

    def list_instances(self, scope: RuntimeScope) -> list[BrowserInstance]:
        self._require(scope, "read")
        return [
            item
            for item in self.instances.values()
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def dashboard(self, scope: RuntimeScope) -> dict[str, Any]:
        instances = self.list_instances(scope)
        instance_ids = {item.id for item in instances}
        contexts = [
            item for item in self.contexts.values() if item.instance_id in instance_ids
        ]
        context_ids = {item.id for item in contexts}
        pages = [item for item in self.pages.values() if item.context_id in context_ids]
        return {
            "sections": [
                "Browser Instances",
                "Profiles",
                "Account Bindings",
                "Pool",
                "Queue",
                "Health",
                "Sessions",
                "Storage",
                "Recovery",
                "Failures",
                "Statistics",
            ],
            "instances": len(instances),
            "profiles": sum(
                p.tenant == scope.tenant and p.workspace == scope.workspace
                for p in self.profiles.values()
            ),
            "account_bindings": sum(bool(item.account_reference) for item in instances),
            "pool": {
                "minimum": self.minimum_pool_size,
                "maximum": self.maximum_pool_size,
                "active": sum(
                    item.status is BrowserStatus.RUNNING for item in instances
                ),
                "idle": sum(item.status is BrowserStatus.IDLE for item in instances),
            },
            "queue": sum(
                item.tenant == scope.tenant and item.workspace == scope.workspace
                for item in self._queue
                if not item.cancelled
            ),
            "contexts": len(contexts),
            "pages": len(pages),
            "health": len(instance_ids & self.health_records.keys()),
            "sessions": sum(bool(item.storage_reference) for item in contexts),
            "storage": sum(bool(item.storage_reference) for item in contexts),
            "recovery": len(
                [r for r in self.recoveries if r.instance_id in instance_ids]
            ),
            "failures": sum(item.status is BrowserStatus.FAILED for item in instances),
            "statistics": self.metrics.snapshot(),
            "kill_switch": self.kill_switch,
        }
