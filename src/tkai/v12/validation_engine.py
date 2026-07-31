"""Comprehensive bounded V12 metadata validation."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, cast

from .api import FORBIDDEN_METHODS, GET_ROUTES, openapi_contract
from .platform import COMPONENTS, V12Platform


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    checks: tuple[str, ...]
    failures: tuple[str, ...]
    duration_seconds: float


def validate_platform() -> ValidationResult:
    started = perf_counter()
    checks = (
        "component-inventory",
        "metadata-integrity",
        "reference-integrity",
        "get-only-api",
        "forbidden-endpoint-absence",
        "local-first",
        "read-only",
        "execution-disabled",
        "version-compatibility",
    )
    failures: list[str] = []
    platform = V12Platform()
    if platform.overview()["component_count"] != len(COMPONENTS):
        failures.append("component inventory mismatch")
    paths = cast(dict[str, dict[str, Any]], openapi_contract()["paths"])
    if tuple(paths) != GET_ROUTES:
        failures.append("OpenAPI path inventory mismatch")
    for path, operations in paths.items():
        if set(operations) != {"get"}:
            failures.append(f"non-GET operation: {path}")
    if set(FORBIDDEN_METHODS) != {"POST", "PUT", "PATCH", "DELETE"}:
        failures.append("forbidden method policy mismatch")
    executions = (
        cast(dict[str, bool], item.projection()["execution"]) for item in COMPONENTS
    )
    if any(execution["enabled"] for execution in executions):
        failures.append("executable component detected")
    return ValidationResult(
        not failures, checks, tuple(failures), perf_counter() - started
    )
