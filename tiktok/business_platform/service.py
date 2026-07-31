"""Integrated, non-executing TKAI Business Platform product service."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .models import BusinessScope, MetadataRecord, ModuleDefinition
from .repository import BusinessRepository

MODULES: tuple[ModuleDefinition, ...] = (
    ModuleDefinition(
        "accounts",
        "Account Center",
        (
            "inventory",
            "cookies",
            "sessions",
            "browser_profiles",
            "devices",
            "proxies",
            "tags",
            "groups",
            "lifecycle",
            "health",
            "imports",
            "exports",
        ),
        ("search", "filter", "batch_metadata", "dashboard", "api"),
        False,
    ),
    ModuleDefinition(
        "browsers",
        "Browser Center",
        (
            "profiles",
            "chromium",
            "playwright",
            "user_data_directories",
            "health",
            "inventory",
        ),
        ("search", "filter", "reference_management"),
    ),
    ModuleDefinition(
        "proxies",
        "Proxy Center",
        (
            "http",
            "https",
            "socks5",
            "regions",
            "providers",
            "health",
            "availability",
            "rotation_policies",
        ),
        ("search", "filter", "reference_management"),
    ),
    ModuleDefinition(
        "tasks",
        "Task Center",
        (
            "like",
            "follow",
            "favorite",
            "comment",
            "browse",
            "search",
            "message",
            "upload",
            "collection",
            "templates",
            "groups",
            "history",
            "audit",
        ),
        ("search", "filter", "planning"),
    ),
    ModuleDefinition(
        "content",
        "Content Center",
        ("drafts", "videos", "images", "captions", "hashtags", "schedules", "library"),
        ("search", "filter", "metadata_management"),
    ),
    ModuleDefinition(
        "data",
        "Data Center",
        ("statistics", "kpis", "reports", "charts", "trends", "dashboard", "exports"),
        ("aggregate", "compare", "visualize"),
    ),
    ModuleDefinition(
        "ai-studio",
        "AI Studio",
        (
            "prompts",
            "skills",
            "agents",
            "workflows",
            "knowledge",
            "models",
            "memory",
            "validation",
        ),
        ("catalog", "validation", "reference_management"),
    ),
    ModuleDefinition(
        "admin",
        "Enterprise Admin",
        (
            "organizations",
            "teams",
            "users",
            "roles",
            "permissions",
            "audit",
            "settings",
            "policies",
        ),
        ("rbac", "governance", "tenant_isolation"),
        False,
    ),
)


class BusinessPlatform:
    """Tenant-scoped product catalog that never launches, switches, or executes."""

    version = "2.0.0"
    compatibility = ("v6", "v7", "v8", "v9", "v10", "v11", "v12")

    SECRET_KEYS = {
        "password",
        "cookie",
        "cookies",
        "session",
        "token",
        "secret",
        "credential",
    }

    def __init__(self, database: str | Path = ":memory:") -> None:
        self._records: tuple[MetadataRecord, ...] = ()
        self.repository = BusinessRepository(database)

    @classmethod
    def redact(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: "[REDACTED]"
                if any(word in key.casefold() for word in cls.SECRET_KEYS)
                else cls.redact(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [cls.redact(item) for item in value]
        return value

    @staticmethod
    def _validate(scope: BusinessScope, payload: dict[str, Any]) -> None:
        if not scope.tenant.strip() or not scope.workspace.strip():
            raise ValueError("Tenant and workspace are required.")
        for field in ("id", "name", "module", "kind"):
            if not str(payload.get(field, "")).strip():
                raise ValueError(f"{field} is required.")
        if payload["module"] not in {item.id for item in MODULES}:
            raise ValueError("Unknown business module.")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", str(payload["id"])):
            raise ValueError("Invalid record id.")
        raw = json.dumps(payload, sort_keys=True).casefold()
        if any(
            f'"{key}":' in raw
            for key in ("password", "cookie", "session", "token", "secret")
        ):
            raise ValueError(
                "Secret values are forbidden; store an opaque reference instead."
            )

    def create(self, scope: BusinessScope, payload: dict[str, Any]) -> dict[str, Any]:
        self._validate(scope, payload)
        now = self.repository.now()
        with self.repository.transaction() as db:
            db.execute(
                """INSERT INTO business_records
                (tenant,workspace,id,module,kind,name,status,health,owner,group_name,
                 tags_json,references_json,metadata_json,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    scope.tenant,
                    scope.workspace,
                    payload["id"],
                    payload["module"],
                    payload["kind"],
                    payload["name"],
                    payload.get("status", "active"),
                    payload.get("health", "unknown"),
                    payload.get("owner", scope.actor),
                    payload.get("group", ""),
                    json.dumps(payload.get("tags", [])),
                    json.dumps(payload.get("references", {})),
                    json.dumps(self.redact(payload.get("metadata", {}))),
                    now,
                    now,
                ),
            )
            self._audit(db, scope, "create", payload["id"], payload["module"])
        return self.get(scope, payload["id"])

    def get(self, scope: BusinessScope, record_id: str) -> dict[str, Any]:
        row = self.repository._shared.execute(
            "SELECT * FROM business_records WHERE tenant=? AND workspace=? AND id=?",
            (scope.tenant, scope.workspace, record_id),
        ).fetchone()
        if row is None:
            raise KeyError("Record not found.")
        return self.redact(self.repository.decode(row))

    def update(
        self, scope: BusinessScope, record_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        current = self.get(scope, record_id)
        merged = {**current, **payload, "id": record_id}
        self._validate(scope, merged)
        allowed = {
            "name",
            "kind",
            "status",
            "health",
            "owner",
            "group",
            "tags",
            "references",
            "metadata",
        }
        values = {key: merged[key] for key in allowed if key in merged}
        with self.repository.transaction() as db:
            db.execute(
                """UPDATE business_records SET
                name=?,kind=?,status=?,health=?,owner=?,group_name=?,
                tags_json=?,references_json=?,metadata_json=?,updated_at=?
                WHERE tenant=? AND workspace=? AND id=?""",
                (
                    values["name"],
                    values["kind"],
                    values["status"],
                    values["health"],
                    values["owner"],
                    values["group"],
                    json.dumps(values["tags"]),
                    json.dumps(values["references"]),
                    json.dumps(self.redact(values["metadata"])),
                    self.repository.now(),
                    scope.tenant,
                    scope.workspace,
                    record_id,
                ),
            )
            self._audit(db, scope, "update", record_id, current["module"])
        return self.get(scope, record_id)

    def archive(self, scope: BusinessScope, record_id: str) -> dict[str, Any]:
        current = self.get(scope, record_id)
        with self.repository.transaction() as db:
            db.execute(
                "UPDATE business_records SET archived=1,status='archived',"
                "updated_at=? WHERE tenant=? AND workspace=? AND id=?",
                (self.repository.now(), scope.tenant, scope.workspace, record_id),
            )
            self._audit(db, scope, "archive", record_id, current["module"])
        return self.get(scope, record_id)

    def _audit(
        self,
        db: Any,
        scope: BusinessScope,
        action: str,
        resource_id: str,
        module: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        db.execute(
            "INSERT INTO business_audit(tenant,workspace,actor,action,resource_id,"
            "module,at,details_json) VALUES(?,?,?,?,?,?,?,?)",
            (
                scope.tenant,
                scope.workspace,
                scope.actor,
                action,
                resource_id,
                module,
                self.repository.now(),
                json.dumps(self.redact(details or {})),
            ),
        )

    def inventory(
        self,
        scope: BusinessScope,
        *,
        module: str = "",
        kind: str = "",
        status: str = "",
        health: str = "",
        tag: str = "",
        group: str = "",
        query: str = "",
    ) -> dict[str, Any]:
        query_folded = query.casefold()
        persisted = self.repository._shared.execute(
            "SELECT * FROM business_records WHERE tenant=? AND workspace=? "
            "AND archived=0",
            (scope.tenant, scope.workspace),
        ).fetchall()
        source = list(self._records) + [
            self.repository.decode(row) for row in persisted
        ]
        items = [
            item
            for item in source
            if (item.tenant if isinstance(item, MetadataRecord) else item["tenant"])
            == scope.tenant
            and (
                item.workspace
                if isinstance(item, MetadataRecord)
                else item["workspace"]
            )
            == scope.workspace
            and (
                not module
                or (item.module if isinstance(item, MetadataRecord) else item["module"])
                == module
            )
            and (
                not kind
                or (item.kind if isinstance(item, MetadataRecord) else item["kind"])
                == kind
            )
            and (
                not status
                or (item.status if isinstance(item, MetadataRecord) else item["status"])
                == status
            )
            and (
                not health
                or (
                    item.health.value
                    if isinstance(item, MetadataRecord)
                    else item["health"]
                )
                == health
            )
            and (
                not tag
                or tag
                in (item.tags if isinstance(item, MetadataRecord) else item["tags"])
            )
            and (
                not group
                or (item.group if isinstance(item, MetadataRecord) else item["group"])
                == group
            )
            and (
                not query_folded or query_folded in f"{item.id} {item.name}".casefold()
                if isinstance(item, MetadataRecord)
                else not query_folded
                or query_folded in f"{item['id']} {item['name']}".casefold()
            )
        ]
        data = [
            item.to_dict() if isinstance(item, MetadataRecord) else self.redact(item)
            for item in items
        ]
        return {
            "data": data,
            "total": len(items),
            "error": None,
        }

    def modules(self) -> dict[str, Any]:
        return {
            "data": [item.to_dict() for item in MODULES],
            "total": len(MODULES),
            "error": None,
        }

    def module(self, module_id: str, scope: BusinessScope) -> dict[str, Any]:
        definition = next(item for item in MODULES if item.id == module_id)
        inventory = self.inventory(scope, module=module_id)
        return {
            "module": definition.to_dict(),
            "inventory": inventory,
            "controls": {
                "execution": False,
                "publishing": False,
                "browser_launch": False,
                "proxy_switching": False,
            },
        }

    def dashboard(self, scope: BusinessScope) -> dict[str, Any]:
        records = self.inventory(scope)["data"]
        health = Counter(str(item["health"]) for item in records)
        totals = Counter(str(item["module"]) for item in records)
        return {
            "product": "TKAI Business Platform",
            "version": self.version,
            "navigation": (
                "home",
                "accounts",
                "browsers",
                "proxies",
                "tasks",
                "content",
                "data",
                "health",
                "audit",
                "settings",
            ),
            "modules": {
                item.id: {
                    "title": item.title,
                    "resources": len(item.resources),
                    "records": totals[item.id],
                }
                for item in MODULES
            },
            "health": dict(health),
            "records": len(records),
            "compatibility": self.compatibility,
            "safety": {"metadata_only": True, "execution_routes": 0, "advisory": True},
        }

    def health(self, scope: BusinessScope) -> dict[str, Any]:
        dashboard = self.dashboard(scope)
        return {
            "status": "healthy",
            "checks": {
                "catalog": "pass",
                "tenant_isolation": "pass",
                "execution_boundary": "pass",
            },
            "inventory": dashboard["health"],
        }

    def audit(self, scope: BusinessScope) -> dict[str, Any]:
        rows = self.repository._shared.execute(
            "SELECT * FROM business_audit WHERE tenant=? AND workspace=? "
            "ORDER BY sequence DESC LIMIT 500",
            (scope.tenant, scope.workspace),
        ).fetchall()
        return {
            "data": [
                {**dict(row), "details": json.loads(row["details_json"])}
                for row in rows
            ],
            "total": len(rows),
            "scope": {"tenant": scope.tenant, "workspace": scope.workspace},
            "immutable": True,
        }

    def settings(self, scope: BusinessScope) -> dict[str, Any]:
        return {
            "tenant": scope.tenant,
            "workspace": scope.workspace,
            "locale": "en",
            "timezone": "UTC",
            "execution_enabled": False,
        }

    def export_metadata(self, scope: BusinessScope, module: str = "") -> dict[str, Any]:
        inventory = self.inventory(scope, module=module)
        return {
            "format": "json",
            "generated": False,
            "advisory": True,
            "record_count": inventory["total"],
            "filters": {"module": module},
        }

    def add_metadata(self, *records: MetadataRecord) -> None:
        """Seed metadata through trusted composition code, never HTTP execution."""
        keys = {(item.tenant, item.workspace, item.id) for item in self._records}
        for record in records:
            key = (record.tenant, record.workspace, record.id)
            if key in keys:
                raise ValueError(
                    "Metadata record ID must be unique within a workspace."
                )
            keys.add(key)
        self._records += records
