"""Bounded browser and Account Center integration interfaces."""

from __future__ import annotations

from typing import Any, Protocol

from .models import BrowserInstance


class BrowserDriver(Protocol):
    def launch(self, instance: BrowserInstance) -> str: ...
    def stop(self, process_reference: str) -> None: ...


class AccountStatusPort(Protocol):
    def update_login_status(
        self,
        account_reference: str,
        tenant: str,
        workspace: str,
        *,
        logged_in: bool,
        expired: bool,
        risk: str,
    ) -> None: ...

    def auto_pause(
        self, account_reference: str, tenant: str, workspace: str, reason: str
    ) -> None: ...


class ReferenceBrowserDriver:
    """Deterministic test double; it never launches a local executable."""

    def __init__(self) -> None:
        self.running: set[str] = set()

    def launch(self, instance: BrowserInstance) -> str:
        reference = f"process://{instance.id}"
        self.running.add(reference)
        return reference

    def stop(self, process_reference: str) -> None:
        self.running.discard(process_reference)


class NullAccountStatusPort:
    def update_login_status(
        self,
        account_reference: str,
        tenant: str,
        workspace: str,
        *,
        logged_in: bool,
        expired: bool,
        risk: str,
    ) -> None:
        return None

    def auto_pause(
        self, account_reference: str, tenant: str, workspace: str, reason: str
    ) -> None:
        return None


def sanitized_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    blocked = {"password", "secret", "cookie", "session", "token", "credential"}
    return {
        key: value
        for key, value in metadata.items()
        if not any(term in key.casefold() for term in blocked)
    }
