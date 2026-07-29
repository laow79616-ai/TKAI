"""Bounded, deterministic V7 extension and plugin metadata framework."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import replace
from threading import RLock
from typing import TypeVar

from .contracts import (
    CompatibilityResult,
    Dependency,
    DependencyResolution,
    ExtensionManifest,
    ExtensionStatus,
    Lifecycle,
    PluginManifest,
    Scope,
    ValidationIssue,
    ValidationResult,
    ValidationStatus,
    now_utc,
    serialize,
)

T = TypeVar("T")
MAX_RESULTS = 1000
ALLOWED_PERMISSIONS = frozenset(
    {
        "audit:read",
        "catalog:read",
        "configuration:read",
        "events:read",
        "health:read",
        "metrics:read",
        "registry:read",
        "state:read",
    }
)
LIFECYCLE_TRANSITIONS: Mapping[Lifecycle, frozenset[Lifecycle]] = {
    Lifecycle.DISCOVERED: frozenset({Lifecycle.REGISTERED, Lifecycle.ARCHIVED}),
    Lifecycle.REGISTERED: frozenset({Lifecycle.VALIDATED, Lifecycle.DISABLED}),
    Lifecycle.VALIDATED: frozenset({Lifecycle.COMPATIBLE, Lifecycle.DISABLED}),
    Lifecycle.COMPATIBLE: frozenset({Lifecycle.AVAILABLE, Lifecycle.DISABLED}),
    Lifecycle.AVAILABLE: frozenset(
        {Lifecycle.DISABLED, Lifecycle.DEPRECATED, Lifecycle.RETIRED}
    ),
    Lifecycle.DISABLED: frozenset(
        {Lifecycle.AVAILABLE, Lifecycle.DEPRECATED, Lifecycle.RETIRED}
    ),
    Lifecycle.DEPRECATED: frozenset({Lifecycle.RETIRED, Lifecycle.ARCHIVED}),
    Lifecycle.RETIRED: frozenset({Lifecycle.ARCHIVED}),
    Lifecycle.ARCHIVED: frozenset(),
}
METRIC_NAMES = (
    "v7_extensions_discovered_total",
    "v7_extensions_registered_total",
    "v7_plugins_registered_total",
    "v7_extension_validations_total",
    "v7_extension_validation_failures_total",
    "v7_extension_compatibility_checks_total",
    "v7_extension_dependency_resolutions_total",
    "v7_extension_security_rejections_total",
    "v7_extension_health_status",
)


class ExtensionFrameworkError(RuntimeError):
    pass


class DuplicateReferenceError(ExtensionFrameworkError):
    pass


class IsolationError(ExtensionFrameworkError):
    pass


class LifecycleError(ExtensionFrameworkError):
    pass


class BoundedStore:
    def __init__(self) -> None:
        self._values: dict[str, object] = {}
        self._lock = RLock()

    def register(self, key: str, value: T) -> T:
        with self._lock:
            if key in self._values:
                raise DuplicateReferenceError(f"already registered: {key}")
            if len(self._values) >= MAX_RESULTS:
                raise ExtensionFrameworkError("registry capacity reached")
            self._values[key] = value
        return value

    def replace(self, key: str, value: T) -> T:
        with self._lock:
            if key not in self._values:
                raise ExtensionFrameworkError(f"unknown reference: {key}")
            self._values[key] = value
        return value

    def get(self, key: str, expected: type[T]) -> T:
        value = self._values.get(key)
        if not isinstance(value, expected):
            raise ExtensionFrameworkError(f"unknown reference: {key}")
        return value

    def values(self, expected: type[T]) -> tuple[T, ...]:
        return tuple(
            value for value in self._values.values() if isinstance(value, expected)
        )[:MAX_RESULTS]


class ExtensionRegistry:
    """Local registry with metadata, capability, and dependency indexes."""

    def __init__(self) -> None:
        self.extensions = BoundedStore()
        self.plugins = BoundedStore()

    def register_extension(self, manifest: ExtensionManifest) -> ExtensionManifest:
        return self.extensions.register(manifest.extension_id, manifest)

    def register_plugin(self, manifest: PluginManifest) -> PluginManifest:
        return self.plugins.register(manifest.plugin_id, manifest)

    def extensions_for(self, scope: Scope) -> tuple[ExtensionManifest, ...]:
        return tuple(
            item
            for item in self.extensions.values(ExtensionManifest)
            if item.scope == scope
        )

    def plugins_for(self, scope: Scope) -> tuple[PluginManifest, ...]:
        return tuple(
            item for item in self.plugins.values(PluginManifest) if item.scope == scope
        )

    def by_capability(
        self, capability: str, scope: Scope
    ) -> tuple[ExtensionManifest, ...]:
        return tuple(
            item
            for item in self.extensions_for(scope)
            if capability in item.capabilities
        )

    def by_dependency(
        self, extension_id: str, scope: Scope
    ) -> tuple[ExtensionManifest, ...]:
        return tuple(
            item
            for item in self.extensions_for(scope)
            if extension_id in {dep.extension_id for dep in item.dependencies}
        )


def _version_tuple(value: str) -> tuple[int, int, int]:
    core = value.split("+", 1)[0].split("-", 1)[0]
    major, minor, patch = core.split(".")
    return int(major), int(minor), int(patch)


def version_satisfies(version: str, constraint: str) -> bool:
    """Evaluate a bounded subset of semantic-version constraints."""
    if constraint.strip() in {"", "*"}:
        return True
    actual = _version_tuple(version)
    for clause in constraint.split(","):
        match = re.fullmatch(r"\s*(>=|<=|>|<|==|\^|~)?\s*(\d+\.\d+\.\d+)\s*", clause)
        if match is None:
            return False
        operator, expected_text = match.groups()
        expected = _version_tuple(expected_text)
        comparisons = {
            None: actual == expected,
            "==": actual == expected,
            ">=": actual >= expected,
            "<=": actual <= expected,
            ">": actual > expected,
            "<": actual < expected,
            "^": actual >= expected and actual < (expected[0] + 1, 0, 0),
            "~": actual >= expected and actual < (expected[0], expected[1] + 1, 0),
        }
        if not comparisons[operator]:
            return False
    return True


class ExtensionValidator:
    checked_rules = (
        "manifest",
        "contract",
        "dependency",
        "permission",
        "compatibility",
        "signature-metadata",
        "reference-integrity",
    )

    def validate(
        self,
        manifest: ExtensionManifest | PluginManifest,
        registry: ExtensionRegistry,
    ) -> ValidationResult:
        issues: list[ValidationIssue] = []
        unknown_permissions = manifest.permissions - ALLOWED_PERMISSIONS
        if unknown_permissions:
            issues.append(
                ValidationIssue(
                    "permission",
                    "permissions",
                    "permissions outside internal allowlist: "
                    f"{sorted(unknown_permissions)}",
                )
            )
        if isinstance(manifest, PluginManifest):
            try:
                extension = registry.extensions.get(
                    manifest.extension_id, ExtensionManifest
                )
                if extension.scope != manifest.scope:
                    issues.append(
                        ValidationIssue(
                            "isolation", "extension_id", "parent scope mismatch"
                        )
                    )
                if manifest.plugin_id not in extension.plugin_ids:
                    issues.append(
                        ValidationIssue(
                            "reference-integrity",
                            "plugin_id",
                            "plugin is not declared by parent extension",
                        )
                    )
            except ExtensionFrameworkError:
                issues.append(
                    ValidationIssue(
                        "reference-integrity", "extension_id", "parent not registered"
                    )
                )
        for dependency in manifest.dependencies:
            self._validate_dependency(manifest, dependency, registry, issues)
        status = ValidationStatus.INVALID if issues else ValidationStatus.VALID
        subject_id = (
            manifest.plugin_id
            if isinstance(manifest, PluginManifest)
            else manifest.extension_id
        )
        return ValidationResult(subject_id, status, tuple(issues), self.checked_rules)

    @staticmethod
    def _validate_dependency(
        manifest: ExtensionManifest | PluginManifest,
        dependency: Dependency,
        registry: ExtensionRegistry,
        issues: list[ValidationIssue],
    ) -> None:
        try:
            target = registry.extensions.get(dependency.extension_id, ExtensionManifest)
        except ExtensionFrameworkError:
            if not dependency.optional:
                issues.append(
                    ValidationIssue(
                        "dependency",
                        dependency.extension_id,
                        "required dependency is missing",
                    )
                )
            return
        if target.scope != manifest.scope:
            issues.append(
                ValidationIssue(
                    "isolation", dependency.extension_id, "dependency scope mismatch"
                )
            )
        if not version_satisfies(target.version, dependency.version_constraint):
            issues.append(
                ValidationIssue(
                    "dependency-version",
                    dependency.extension_id,
                    "dependency version is incompatible",
                )
            )
        if not dependency.required_capabilities.issubset(target.capabilities):
            issues.append(
                ValidationIssue(
                    "dependency-capability",
                    dependency.extension_id,
                    "dependency capability is missing",
                )
            )


class ExtensionFramework:
    """Internal metadata plane; it never loads, installs, or executes code."""

    def __init__(
        self,
        *,
        platform_version: str = "7.0.0",
        platform_capabilities: Iterable[str] = (),
        platform_interfaces: Mapping[str, str] | None = None,
    ) -> None:
        self.platform_version = platform_version
        self.platform_capabilities = frozenset(platform_capabilities)
        self.platform_interfaces = dict(platform_interfaces or {})
        self.registry = ExtensionRegistry()
        self.validator = ExtensionValidator()
        self.validations = BoundedStore()
        self.compatibility_results = BoundedStore()
        self.dependency_results = BoundedStore()
        self.audit: list[Mapping[str, object]] = []
        self.traces: list[Mapping[str, object]] = []
        self.metric_values: Counter[str] = Counter({name: 0 for name in METRIC_NAMES})

    def discover_static(
        self, manifests: Iterable[ExtensionManifest]
    ) -> tuple[ExtensionManifest, ...]:
        discovered: list[ExtensionManifest] = []
        for manifest in manifests:
            item = replace(
                manifest,
                lifecycle=Lifecycle.DISCOVERED,
                status=ExtensionStatus.UNKNOWN,
                updated_at=now_utc(),
            )
            self.registry.register_extension(item)
            self.metric_values["v7_extensions_discovered_total"] += 1
            self._record("discovered", item.extension_id, item.scope)
            discovered.append(item)
        return tuple(discovered)

    def register_extension(
        self, manifest: ExtensionManifest
    ) -> ExtensionManifest:
        item = replace(
            manifest, lifecycle=Lifecycle.REGISTERED, updated_at=now_utc()
        )
        result = self.registry.register_extension(item)
        self.metric_values["v7_extensions_registered_total"] += 1
        self._record("registered", item.extension_id, item.scope)
        return result

    def register_plugin(self, manifest: PluginManifest) -> PluginManifest:
        parent = self.registry.extensions.get(
            manifest.extension_id, ExtensionManifest
        )
        self._require_scope(parent.scope, manifest.scope)
        if manifest.plugin_id not in parent.plugin_ids:
            raise ExtensionFrameworkError("plugin is not declared by parent extension")
        item = replace(manifest, lifecycle=Lifecycle.REGISTERED)
        result = self.registry.register_plugin(item)
        self.metric_values["v7_plugins_registered_total"] += 1
        self._record("plugin-registered", item.plugin_id, item.scope)
        return result

    def validate(
        self, subject_id: str, *, plugin: bool = False
    ) -> ValidationResult:
        manifest = self._subject(subject_id, plugin)
        result = self.validator.validate(manifest, self.registry)
        self._upsert(self.validations, f"{plugin}:{subject_id}", result)
        self.metric_values["v7_extension_validations_total"] += 1
        if result.status is ValidationStatus.INVALID:
            self.metric_values["v7_extension_validation_failures_total"] += 1
            if any(
                issue.code in {"permission", "isolation"} for issue in result.issues
            ):
                self.metric_values["v7_extension_security_rejections_total"] += 1
        self._record("validated", subject_id, manifest.scope)
        return result

    def check_compatibility(
        self, subject_id: str, *, plugin: bool = False
    ) -> CompatibilityResult:
        manifest = self._subject(subject_id, plugin)
        contract = manifest.compatibility
        platform = version_satisfies(
            self.platform_version, contract.platform_constraint
        )
        capabilities = contract.required_capabilities.issubset(
            self.platform_capabilities
        )
        interfaces = all(
            name in self.platform_interfaces
            and version_satisfies(self.platform_interfaces[name], constraint)
            for name, constraint in contract.required_interfaces.items()
        )
        resolution = self.resolve_dependencies(manifest)
        reasons = tuple(
            label
            for valid, label in (
                (platform, "platform-version"),
                (capabilities, "platform-capabilities"),
                (interfaces, "interfaces"),
                (resolution.satisfied, "dependencies"),
            )
            if not valid
        )
        result = CompatibilityResult(
            subject_id,
            not reasons,
            platform,
            capabilities,
            interfaces,
            resolution.satisfied,
            reasons,
            contract.migration_metadata,
        )
        self._upsert(self.compatibility_results, f"{plugin}:{subject_id}", result)
        self.metric_values["v7_extension_compatibility_checks_total"] += 1
        self._record("compatibility-checked", subject_id, manifest.scope)
        return result

    def resolve_dependencies(
        self, manifest: ExtensionManifest | PluginManifest
    ) -> DependencyResolution:
        ordered: list[str] = []
        missing: list[str] = []
        incompatible: list[str] = []
        cycles: list[tuple[str, ...]] = []
        visiting: list[str] = []
        visited: set[str] = set()

        def visit(dependency: Dependency) -> None:
            if dependency.extension_id in visiting:
                start = visiting.index(dependency.extension_id)
                cycles.append(tuple(visiting[start:] + [dependency.extension_id]))
                return
            try:
                target = self.registry.extensions.get(
                    dependency.extension_id, ExtensionManifest
                )
            except ExtensionFrameworkError:
                if not dependency.optional:
                    missing.append(dependency.extension_id)
                return
            if target.scope != manifest.scope or not version_satisfies(
                target.version, dependency.version_constraint
            ):
                incompatible.append(dependency.extension_id)
                return
            if not dependency.required_capabilities.issubset(target.capabilities):
                incompatible.append(dependency.extension_id)
                return
            if target.extension_id in visited:
                return
            visiting.append(target.extension_id)
            for child in target.dependencies:
                visit(child)
            visiting.pop()
            visited.add(target.extension_id)
            ordered.append(target.extension_id)

        for dependency in manifest.dependencies:
            visit(dependency)
        subject_id = (
            manifest.plugin_id
            if isinstance(manifest, PluginManifest)
            else manifest.extension_id
        )
        result = DependencyResolution(
            subject_id,
            tuple(ordered),
            tuple(sorted(set(missing))),
            tuple(sorted(set(incompatible))),
            tuple(cycles),
            not missing and not incompatible and not cycles,
        )
        self._upsert(self.dependency_results, subject_id, result)
        self.metric_values["v7_extension_dependency_resolutions_total"] += 1
        return result

    def transition_extension(
        self, extension_id: str, lifecycle: Lifecycle, scope: Scope
    ) -> ExtensionManifest:
        current = self.registry.extensions.get(extension_id, ExtensionManifest)
        self._require_scope(current.scope, scope)
        if lifecycle not in LIFECYCLE_TRANSITIONS[current.lifecycle]:
            raise LifecycleError(
                f"invalid lifecycle transition: {current.lifecycle.value} -> "
                f"{lifecycle.value}"
            )
        status = {
            Lifecycle.VALIDATED: ExtensionStatus.VALID,
            Lifecycle.COMPATIBLE: ExtensionStatus.COMPATIBLE,
            Lifecycle.AVAILABLE: ExtensionStatus.AVAILABLE,
            Lifecycle.DISABLED: ExtensionStatus.DISABLED,
        }.get(lifecycle, current.status)
        updated = replace(
            current, lifecycle=lifecycle, status=status, updated_at=now_utc()
        )
        self.registry.extensions.replace(extension_id, updated)
        self._record(f"lifecycle:{lifecycle.value}", extension_id, scope)
        return updated

    def lookup_metadata(
        self, query: str, scope: Scope
    ) -> tuple[ExtensionManifest, ...]:
        term = query.casefold()
        return tuple(
            item
            for item in self.registry.extensions_for(scope)
            if term
            in " ".join(
                (
                    item.extension_id,
                    item.name,
                    item.description,
                    item.category,
                    item.owner,
                )
            ).casefold()
        )

    def projection(self, section: str, scope: Scope) -> object:
        extensions = self.registry.extensions_for(scope)
        plugins = self.registry.plugins_for(scope)
        subject_ids = {item.extension_id for item in extensions} | {
            item.plugin_id for item in plugins
        }
        projections: dict[str, object] = {
            "catalog": extensions,
            "registry": extensions,
            "plugins": plugins,
            "dependencies": tuple(
                item
                for item in self.dependency_results.values(DependencyResolution)
                if item.subject_id in subject_ids
            ),
            "compatibility": tuple(
                item
                for item in self.compatibility_results.values(CompatibilityResult)
                if item.subject_id in subject_ids
            ),
            "validation": tuple(
                item
                for item in self.validations.values(ValidationResult)
                if item.subject_id in subject_ids
            ),
            "packages": tuple(
                item.package for item in extensions if item.package is not None
            ),
            "signatures": tuple(
                item.signature for item in extensions if item.signature is not None
            ),
            "health": {
                "status": "healthy",
                "liveness": True,
                "readiness": True,
                "extensions": {
                    item.extension_id: serialize(item.health) for item in extensions
                },
                "metadata_only": True,
                "remote_discovery": False,
                "code_execution": False,
            },
            "metrics": dict(self.metric_values),
            "audit": tuple(
                item
                for item in self.audit
                if item["scope"]
                == f"{scope.tenant}/{scope.workspace}/{scope.namespace}"
            ),
        }
        if section not in projections:
            raise ExtensionFrameworkError(f"unknown projection: {section}")
        return serialize(projections[section])

    def _subject(
        self, subject_id: str, plugin: bool
    ) -> ExtensionManifest | PluginManifest:
        if plugin:
            return self.registry.plugins.get(subject_id, PluginManifest)
        return self.registry.extensions.get(subject_id, ExtensionManifest)

    @staticmethod
    def _upsert(store: BoundedStore, key: str, value: object) -> None:
        if key in store._values:
            store.replace(key, value)
        else:
            store.register(key, value)

    def _record(self, action: str, reference: str, scope: Scope) -> None:
        event = {
            "action": action,
            "reference": reference,
            "scope": f"{scope.tenant}/{scope.workspace}/{scope.namespace}",
            "timestamp": now_utc().isoformat(),
            "safe": True,
        }
        self.audit.append(event)
        self.traces.append(
            {
                "hook": "v7.extension_framework",
                "action": action,
                "reference": reference,
                "timestamp": event["timestamp"],
            }
        )

    @staticmethod
    def _require_scope(actual: Scope, requested: Scope) -> None:
        if actual != requested:
            raise IsolationError("tenant, workspace, or namespace isolation violation")


GLOBAL_EXTENSION_FRAMEWORK = ExtensionFramework()
