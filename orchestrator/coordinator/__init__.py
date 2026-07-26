"""Agent, application, workflow, resource, and limit coordination."""

from __future__ import annotations

from collections import defaultdict


class Coordinator:
    def __init__(self, concurrency: int = 8, per_tenant: int = 4) -> None:
        self.concurrency = concurrency
        self.per_tenant = per_tenant
        self._active = 0
        self._tenant_active: dict[str, int] = defaultdict(int)

    def acquire(self, tenant: str) -> None:
        if self._active >= self.concurrency:
            raise RuntimeError("Global execution limit reached.")
        if self._tenant_active[tenant] >= self.per_tenant:
            raise RuntimeError("Tenant execution limit reached.")
        self._active += 1
        self._tenant_active[tenant] += 1

    def release(self, tenant: str) -> None:
        self._active = max(0, self._active - 1)
        self._tenant_active[tenant] = max(0, self._tenant_active[tenant] - 1)

    def snapshot(self) -> dict[str, object]:
        return {"active": self._active, "tenants": dict(self._tenant_active)}
