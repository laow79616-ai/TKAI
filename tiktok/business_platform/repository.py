"""SQLite persistence for Business Platform V2 management metadata."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2


class BusinessRepository:
    """Small transactional repository with mandatory tenant/workspace keys."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self._shared = sqlite3.connect(self.path, check_same_thread=False)
        self._shared.row_factory = sqlite3.Row
        self._initialize(self._shared)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self._shared
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    def _initialize(self, connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS business_records (
              tenant TEXT NOT NULL, workspace TEXT NOT NULL, id TEXT NOT NULL,
              module TEXT NOT NULL, kind TEXT NOT NULL, name TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'active',
              health TEXT NOT NULL DEFAULT 'unknown',
              owner TEXT NOT NULL DEFAULT '', group_name TEXT NOT NULL DEFAULT '',
              tags_json TEXT NOT NULL DEFAULT '[]',
              references_json TEXT NOT NULL DEFAULT '{}',
              metadata_json TEXT NOT NULL DEFAULT '{}',
              archived INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
              PRIMARY KEY (tenant, workspace, id)
            );
            CREATE INDEX IF NOT EXISTS ix_business_scope_module
              ON business_records(tenant, workspace, module, archived, status);
            CREATE INDEX IF NOT EXISTS ix_business_kind
              ON business_records(tenant, workspace, module, kind);
            CREATE TABLE IF NOT EXISTS business_audit (
              sequence INTEGER PRIMARY KEY AUTOINCREMENT, tenant TEXT NOT NULL,
              workspace TEXT NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL,
              resource_id TEXT NOT NULL, module TEXT NOT NULL, at TEXT NOT NULL,
              details_json TEXT NOT NULL DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS ix_business_audit_scope
              ON business_audit(tenant, workspace, sequence DESC);
            CREATE TABLE IF NOT EXISTS business_settings (
              tenant TEXT NOT NULL, workspace TEXT NOT NULL, key TEXT NOT NULL,
              value_json TEXT NOT NULL, updated_at TEXT NOT NULL,
              PRIMARY KEY (tenant, workspace, key)
            );
            PRAGMA user_version = 2;
            """
        )
        connection.commit()

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def decode(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["group"] = item.pop("group_name")
        item["tags"] = json.loads(item.pop("tags_json"))
        item["references"] = json.loads(item.pop("references_json"))
        item["metadata"] = json.loads(item.pop("metadata_json"))
        item["archived"] = bool(item["archived"])
        return item

    def close(self) -> None:
        self._shared.close()
