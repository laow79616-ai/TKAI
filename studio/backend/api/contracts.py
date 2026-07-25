"""Frozen JSON response envelopes and OpenAPI-compatible schema fragments."""

from __future__ import annotations

from datetime import datetime, timezone


def success(data: object, request_id: str = "local") -> dict[str, object]:
    """Wrap a successful REST payload in the frozen Studio response envelope."""
    return {
        "success": True,
        "data": data,
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def error(code: str, message: str, request_id: str = "local") -> dict[str, object]:
    """Return a stable JSON-safe error envelope without traceback information."""
    return {
        "success": False,
        "error": {"code": code, "message": message},
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


SUCCESS_SCHEMA = {
    "type": "object",
    "required": ["success", "data", "request_id", "timestamp"],
    "properties": {
        "success": {"const": True},
        "data": {},
        "request_id": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
    },
}

ERROR_SCHEMA = {
    "type": "object",
    "required": ["success", "error", "request_id", "timestamp"],
    "properties": {
        "success": {"const": False},
        "error": {
            "type": "object",
            "required": ["code", "message"],
            "properties": {
                "code": {"type": "string"},
                "message": {"type": "string"},
            },
        },
        "request_id": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
    },
}
