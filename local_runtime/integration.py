"""Deterministic TikTok module registry and bounded readiness reporting."""

from __future__ import annotations

import importlib.util
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tiktok.registry import TIKTOK_MODULES
from tkai import __version__

MODULES = tuple((module.key, module.name) for module in TIKTOK_MODULES)


@dataclass(frozen=True)
class ModuleRegistration:
    key: str
    name: str
    package: str
    registered: bool


def module_registry() -> tuple[ModuleRegistration, ...]:
    """Return each expected module once, in dependency order."""
    return tuple(
        ModuleRegistration(
            key=key,
            name=name,
            package=f"tiktok.{key}",
            registered=importlib.util.find_spec(f"tiktok.{key}") is not None,
        )
        for key, name in MODULES
    )


def integration_readiness(app: Any, repository: Path) -> dict[str, Any]:
    """Report local integration state without network or TikTok access."""
    registrations = module_registry()
    route_pairs = [
        (route.path, method)
        for route in getattr(app, "routes", ())
        for method in sorted(getattr(route, "methods", ()) or ())
    ]
    duplicates = sorted(
        f"{method} {path}"
        for path, method in set(route_pairs)
        if route_pairs.count((path, method)) > 1 and method != "HEAD"
    )
    runtime = repository / "runtime"
    checks = {
        "backend": True,
        "database": (runtime / "data").is_dir(),
        "dashboard": (repository / "dashboard" / "frontend").is_dir(),
        "ai_studio": (repository / "studio" / "frontend").is_dir(),
        "runtime_directories": runtime.is_dir(),
        "tiktok_module_registration": all(item.registered for item in registrations),
        "route_uniqueness": not duplicates,
    }
    return {
        "status": "ready" if all(checks.values()) else "not_ready",
        "version": __version__,
        "checks": checks,
        "modules": [asdict(item) for item in registrations],
        "duplicate_routes": duplicates,
        "live_tiktok_required": False,
    }
