"""Deterministic bounded validation for operational metadata."""

from collections.abc import Mapping
from dataclasses import fields, is_dataclass

MAX_REFERENCES = 1_000
MAX_RESULT_SIZE = 100


def validate_record(record: object) -> None:
    if not is_dataclass(record) or isinstance(record, type):
        return
    for item in fields(record):
        value = getattr(record, item.name)
        if isinstance(value, tuple) and len(value) > MAX_REFERENCES:
            raise ValueError(f"{item.name} exceeds bounded reference count")
        if isinstance(value, Mapping) and len(value) > MAX_REFERENCES:
            raise ValueError(f"{item.name} exceeds bounded metadata count")


__all__ = ("MAX_REFERENCES", "MAX_RESULT_SIZE", "validate_record")
