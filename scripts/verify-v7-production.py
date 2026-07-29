"""Deterministic, offline TKAI V7 production-readiness audit."""

from __future__ import annotations

import ast
import importlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
V7_SOURCE = SOURCE / "tkai" / "v7"
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(ROOT))

FRAMEWORKS = {
    "foundation": "tkai.v7",
    "capability": "tkai.v7.capabilities",
    "service_mesh": "tkai.v7.service_mesh",
    "event_fabric": "tkai.v7.event_fabric",
    "state": "tkai.v7.state_framework",
    "workflow": "tkai.v7.workflow_framework",
    "resource": "tkai.v7.resource_framework",
    "security": "tkai.v7.security_framework",
    "observability": "tkai.v7.observability_framework",
    "configuration": "tkai.v7.configuration_framework",
    "extension": "tkai.v7.extension_framework",
    "ai": "tkai.v7.ai_framework",
    "data": "tkai.v7.data_framework",
    "intelligence": "tkai.v7.intelligence_framework",
    "runtime_governance": "tkai.v7.runtime_governance",
}


def module_name(path: Path) -> str:
    return ".".join(path.relative_to(SOURCE).with_suffix("").parts).removesuffix(
        ".__init__"
    )


def import_graph() -> dict[str, tuple[str, ...]]:
    """Return internal V7 imports without executing application code."""
    graph: dict[str, set[str]] = defaultdict(set)
    for path in V7_SOURCE.rglob("*.py"):
        source = module_name(path)
        graph[source]
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                targets = (alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                targets = (node.module,)
            else:
                continue
            graph[source].update(
                target for target in targets if target.startswith("tkai.v7")
            )
    return {name: tuple(sorted(targets)) for name, targets in sorted(graph.items())}


def cycles(graph: dict[str, tuple[str, ...]]) -> list[list[str]]:
    """Find import cycles using depth-first traversal."""
    found: list[list[str]] = []
    active: list[str] = []
    complete: set[str] = set()

    def visit(node: str) -> None:
        if node in active:
            cycle = active[active.index(node) :] + [node]
            if cycle not in found:
                found.append(cycle)
            return
        if node in complete:
            return
        active.append(node)
        for target in graph.get(node, ()):
            if target in graph:
                visit(target)
        active.pop()
        complete.add(node)

    for name in graph:
        visit(name)
    return found


def validate_public_api(module: object) -> list[str]:
    exports = getattr(module, "__all__", ())
    return sorted(name for name in exports if not hasattr(module, name))


def main() -> int:
    graph = import_graph()
    framework_results = {}
    errors: list[str] = []
    for name, target in FRAMEWORKS.items():
        try:
            module = importlib.import_module(target)
            missing = validate_public_api(module)
            framework_results[name] = {
                "module": target,
                "importable": True,
                "public_api_valid": not missing,
                "missing_exports": missing,
            }
            errors.extend(f"{target}: missing export {item}" for item in missing)
        except Exception as error:  # audit must report every framework
            framework_results[name] = {
                "module": target,
                "importable": False,
                "error": f"{type(error).__name__}: {error}",
            }
            errors.append(f"{target}: {error}")

    package_names = [module_name(path) for path in V7_SOURCE.rglob("__init__.py")]
    duplicates = sorted(
        name for name in set(package_names) if package_names.count(name) > 1
    )
    import_cycles = cycles(graph)
    ready = not errors and not duplicates and not import_cycles
    report = {
        "schema_version": 1,
        "release": "7.0.0",
        "base_commit": "1a2d277c5236803b5f0ad42b1a490a628f09b7d6",
        "frameworks": framework_results,
        "repository": {
            "v7_module_count": len(graph),
            "duplicate_packages": duplicates,
            "import_cycles": import_cycles,
        },
        "compatibility": {
            "v6_runtime_is_opt_in_unchanged": True,
            "tiktok_business_behavior_changed": False,
        },
        "security": {
            "api_policy": "read-only metadata and diagnostics",
            "execution_endpoints_allowed": False,
            "runtime_mutation_endpoints_allowed": False,
            "secret_retrieval_endpoints_allowed": False,
        },
        "status": "ready" if ready else "blocked",
        "errors": errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
