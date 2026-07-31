import json
import sqlite3

import pytest

from tiktok.business_platform import BusinessPlatform
from tiktok.business_platform.models import BusinessScope


def payload(record_id: str = "account-1") -> dict[str, object]:
    return {
        "id": record_id,
        "name": "Mock account",
        "module": "accounts",
        "kind": "inventory",
        "tags": ["acceptance"],
        "references": {"proxy": "proxy-ref-1"},
        "metadata": {"notes": "local mock data"},
    }


def test_persistence_scope_redaction_and_audit(tmp_path) -> None:
    path = tmp_path / "business.db"
    scope = BusinessScope("tenant-a", "workspace-a", "admin")
    platform = BusinessPlatform(path)
    created = platform.create(scope, payload())
    assert created["tenant"] == "tenant-a"
    assert platform.inventory(BusinessScope("tenant-b", "workspace-a"))["total"] == 0
    assert platform.audit(scope)["data"][0]["action"] == "create"
    platform.repository.close()
    reopened = BusinessPlatform(path)
    assert reopened.get(scope, "account-1")["name"] == "Mock account"


def test_duplicate_and_secret_values_are_rejected() -> None:
    platform = BusinessPlatform()
    scope = BusinessScope()
    platform.create(scope, payload())
    with pytest.raises(sqlite3.IntegrityError):
        platform.create(scope, payload())
    unsafe = payload("account-2")
    unsafe["metadata"] = {"password": "plaintext"}
    with pytest.raises(ValueError, match="Secret values are forbidden"):
        platform.create(scope, unsafe)


def test_all_modules_create_update_archive_without_execution() -> None:
    platform = BusinessPlatform()
    scope = BusinessScope(actor="operator")
    modules = [item["id"] for item in platform.modules()["data"]]
    for module in modules:
        item = payload(f"{module}-1")
        item["module"] = module
        platform.create(scope, item)
    assert platform.inventory(scope)["total"] == len(modules)
    updated = platform.update(scope, "tasks-1", {"status": "approved"})
    assert updated["status"] == "approved"
    archived = platform.archive(scope, "tasks-1")
    assert archived["archived"] is True
    assert platform.module("tasks", scope)["controls"]["execution"] is False
    assert "plaintext" not in json.dumps(platform.audit(scope))
