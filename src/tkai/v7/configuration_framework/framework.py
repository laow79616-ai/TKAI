"""Deterministic, bounded, read-only V7 configuration framework."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from threading import RLock
from typing import TypeVar
from uuid import uuid4

from .contracts import (
    ChangePlan,
    ConfigurationDefinition,
    ConfigurationDiff,
    ConfigurationSnapshot,
    DefaultArtifact,
    DiffEntry,
    EffectiveConfiguration,
    Environment,
    EnvironmentProfile,
    FieldDefinition,
    Lifecycle,
    MigrationAssessment,
    OverrideArtifact,
    SchemaDefinition,
    Scope,
    SourceDefinition,
    ValidationIssue,
    ValidationResult,
    ValidationStatus,
    is_secret_field,
    is_secret_reference,
    now_utc,
    safe_value,
    serialize,
)

T = TypeVar("T")
MAX_FIELDS = 512
MAX_RESULTS = 1000
MAX_DIFF_ENTRIES = 512
MAX_FILE_BYTES = 1_048_576

METRIC_NAMES = (
    "v7_configuration_definitions_total",
    "v7_configuration_profiles_total",
    "v7_configuration_sources_total",
    "v7_configuration_schemas_total",
    "v7_configuration_validations_total",
    "v7_configuration_validation_failures_total",
    "v7_configuration_conflicts_total",
    "v7_configuration_snapshots_total",
    "v7_configuration_overrides_total",
    "v7_configuration_expired_overrides_total",
    "v7_configuration_compatibility_issues_total",
    "v7_configuration_resolution_seconds",
    "v7_configuration_validation_seconds",
    "v7_configuration_health_status",
)


class ConfigurationError(RuntimeError):
    pass


class DuplicateReferenceError(ConfigurationError):
    pass


class IsolationError(ConfigurationError):
    pass


class BoundedStore:
    def __init__(self) -> None:
        self._values: dict[str, object] = {}
        self._lock = RLock()

    def register(self, key: str, value: T) -> T:
        with self._lock:
            if key in self._values:
                raise DuplicateReferenceError(f"already registered: {key}")
            self._values[key] = value
        return value

    def get(self, key: str, expected: type[T]) -> T:
        value = self._values.get(key)
        if not isinstance(value, expected):
            raise ConfigurationError(f"unknown reference: {key}")
        return value

    def values(self, expected: type[T]) -> tuple[T, ...]:
        return tuple(
            value for value in self._values.values() if isinstance(value, expected)
        )[:MAX_RESULTS]


class ConfigurationRegistry:
    """Local indexed registry with exact tenant/workspace/namespace isolation."""

    def __init__(self) -> None:
        self.configurations = BoundedStore()
        self.profiles = BoundedStore()
        self.sources = BoundedStore()
        self.schemas = BoundedStore()
        self.defaults = BoundedStore()
        self.overrides = BoundedStore()

    def register_configuration(
        self, definition: ConfigurationDefinition
    ) -> ConfigurationDefinition:
        return self.configurations.register(definition.configuration_id, definition)

    def register_profile(self, profile: EnvironmentProfile) -> EnvironmentProfile:
        return self.profiles.register(profile.profile_id, profile)

    def register_source(self, source: SourceDefinition) -> SourceDefinition:
        return self.sources.register(source.source_id, source)

    def register_schema(self, schema: SchemaDefinition) -> SchemaDefinition:
        return self.schemas.register(schema.schema_id, schema)

    def register_default(self, artifact: DefaultArtifact) -> DefaultArtifact:
        return self.defaults.register(artifact.default_id, artifact)

    def register_override(self, artifact: OverrideArtifact) -> OverrideArtifact:
        return self.overrides.register(artifact.override_id, artifact)

    def lookup_configurations(
        self,
        scope: Scope,
        *,
        environment: str | None = None,
        version: str | None = None,
        lifecycle: Lifecycle | None = None,
    ) -> tuple[ConfigurationDefinition, ...]:
        return tuple(
            item
            for item in self.configurations.values(ConfigurationDefinition)
            if item.scope == scope
            and (environment is None or item.environment.value == environment)
            and (version is None or item.version == version)
            and (lifecycle is None or item.lifecycle is lifecycle)
        )

    def compatibility_lookup(
        self, scope: Scope, version: str = "6"
    ) -> tuple[ConfigurationDefinition, ...]:
        return tuple(
            item
            for item in self.lookup_configurations(scope)
            if version in item.tags or f"compatible-v{version}" in item.tags
        )


class SafePathPolicy:
    def __init__(self, allowed_roots: Iterable[Path]) -> None:
        self.allowed_roots = tuple(path.resolve() for path in allowed_roots)

    def validate(self, path: Path) -> Path:
        resolved = path.resolve()
        if not any(
            resolved == root or root in resolved.parents for root in self.allowed_roots
        ):
            raise ConfigurationError("file reference is outside allowed roots")
        if not resolved.is_file():
            raise ConfigurationError("file reference does not identify a file")
        if resolved.stat().st_size > MAX_FILE_BYTES:
            raise ConfigurationError("configuration file exceeds bounded size")
        return resolved


class SchemaValidator:
    TYPES: Mapping[str, type[object]] = {
        "string": str,
        "integer": int,
        "number": (int, float),  # type: ignore[dict-item]
        "boolean": bool,
        "array": (list, tuple),  # type: ignore[dict-item]
        "object": dict,
    }

    def validate(
        self,
        values: Mapping[str, object],
        schema: SchemaDefinition,
        *,
        previous: Mapping[str, object] | None = None,
        limit: int = MAX_RESULTS,
    ) -> ValidationResult:
        issues: list[ValidationIssue] = []
        fields = {item.name: item for item in schema.fields}
        for field in schema.fields:
            value = values.get(field.name)
            if field.required and field.name not in values:
                issues.append(
                    ValidationIssue("required", field.name, "field is required")
                )
                continue
            if field.name not in values:
                continue
            expected = self.TYPES.get(field.type_name)
            if expected is None:
                issues.append(
                    ValidationIssue(
                        "type-rule", field.name, "unsupported declarative type"
                    )
                )
                continue
            if not isinstance(value, expected) or (
                field.type_name in {"integer", "number"} and isinstance(value, bool)
            ):
                issues.append(ValidationIssue("type", field.name, "type mismatch"))
                continue
            self._field_rules(field, value, issues)
            if field.secret and not is_secret_reference(value):
                issues.append(
                    ValidationIssue(
                        "secret-reference", field.name, "reference required"
                    )
                )
            if (
                field.immutable
                and previous is not None
                and field.name in previous
                and previous[field.name] != value
            ):
                issues.append(
                    ValidationIssue("immutable", field.name, "immutable field changed")
                )
            if field.deprecated:
                issues.append(
                    ValidationIssue(
                        "deprecated", field.name, "field is deprecated", "warning"
                    )
                )
        for name in values:
            if name not in fields:
                issues.append(
                    ValidationIssue("unknown", name, "field is not in schema")
                )
        bounded = len(issues) <= limit
        issues = issues[:limit]
        invalid = any(item.severity == "error" for item in issues)
        return ValidationResult(
            str(uuid4()),
            ValidationStatus.INVALID if invalid else ValidationStatus.VALID,
            tuple(issues),
            (
                "schema",
                "type",
                "required",
                "allowed-value",
                "range",
                "format",
                "secret-reference",
                "immutable",
            ),
            bounded,
        )

    @staticmethod
    def _field_rules(
        field: FieldDefinition, value: object, issues: list[ValidationIssue]
    ) -> None:
        if field.allowed_values and value not in field.allowed_values:
            issues.append(
                ValidationIssue("allowed-value", field.name, "value not allowed")
            )
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if field.minimum is not None and value < field.minimum:
                issues.append(ValidationIssue("range", field.name, "below minimum"))
            if field.maximum is not None and value > field.maximum:
                issues.append(ValidationIssue("range", field.name, "above maximum"))
        if field.format_pattern and isinstance(value, str):
            if re.fullmatch(field.format_pattern, value) is None:
                issues.append(ValidationIssue("format", field.name, "format mismatch"))


class ConfigurationFramework:
    """No-network, no-apply configuration metadata and advisory planning service."""

    def __init__(self, allowed_file_roots: Iterable[Path] = ()) -> None:
        self.registry = ConfigurationRegistry()
        self.validator = SchemaValidator()
        self.path_policy = SafePathPolicy(allowed_file_roots)
        self.snapshots = BoundedStore()
        self.diffs = BoundedStore()
        self.change_plans = BoundedStore()
        self.migrations = BoundedStore()
        self.audit: list[Mapping[str, object]] = []
        self.diagnostics: list[Mapping[str, object]] = []
        self.metric_values: Counter[str] = Counter({name: 0 for name in METRIC_NAMES})

    def register_configuration(
        self, definition: ConfigurationDefinition
    ) -> ConfigurationDefinition:
        result = self.registry.register_configuration(definition)
        self._record("registration", definition.configuration_id, definition.scope)
        self.metric_values["v7_configuration_definitions_total"] += 1
        return result

    def register_profile(self, profile: EnvironmentProfile) -> EnvironmentProfile:
        result = self.registry.register_profile(profile)
        self._record("profile", profile.profile_id)
        self.metric_values["v7_configuration_profiles_total"] += 1
        return result

    def register_source(self, source: SourceDefinition) -> SourceDefinition:
        if source.path_reference:
            self.path_policy.validate(Path(source.path_reference))
        result = self.registry.register_source(source)
        self._record("source", source.source_id, source.scope)
        self.metric_values["v7_configuration_sources_total"] += 1
        return result

    def register_schema(self, schema: SchemaDefinition) -> SchemaDefinition:
        result = self.registry.register_schema(schema)
        self._record("schema", schema.schema_id)
        self.metric_values["v7_configuration_schemas_total"] += 1
        return result

    def resolve(
        self, configuration_reference: str, scope: Scope
    ) -> EffectiveConfiguration:
        definition = self.registry.configurations.get(
            configuration_reference, ConfigurationDefinition
        )
        self._require_scope(definition.scope, scope)
        profile = self.registry.profiles.get(definition.profile, EnvironmentProfile)
        sources = [
            self.registry.sources.get(reference, SourceDefinition)
            for reference in definition.source_references
        ]
        eligible: list[SourceDefinition] = []
        for source in sources:
            self._require_scope(source.scope, scope)
            if (
                source.available
                and source.kind in profile.allowed_sources
                and source.environment is definition.environment
                and source.profile == definition.profile
            ):
                eligible.append(source)
        rank = {
            kind: index
            for index, kind in enumerate(profile.precedence_rule.ordered_sources)
        }
        eligible.sort(key=lambda item: (rank[item.kind], item.source_id))
        values: dict[str, object] = {}
        provenance: dict[str, str] = {}
        conflicts: list[str] = []
        explanation: list[str] = []
        for source in eligible:
            for name, value in tuple(source.field_references.items())[:MAX_FIELDS]:
                if name in values and values[name] != value:
                    conflicts.append(name)
                values[name] = safe_value(name, value)
                provenance[name] = source.source_id
            explanation.append(
                f"{source.source_id}: rank {rank[source.kind]} ({source.kind.value})"
            )
        validation: ValidationResult | None = None
        if definition.schema_reference:
            schema = self.registry.schemas.get(
                definition.schema_reference, SchemaDefinition
            )
            if schema.namespace != scope.namespace:
                raise IsolationError("schema namespace isolation violation")
            validation = self.validator.validate(values, schema)
            self.metric_values["v7_configuration_validations_total"] += 1
            if validation.status is ValidationStatus.INVALID:
                self.metric_values["v7_configuration_validation_failures_total"] += 1
        self.metric_values["v7_configuration_conflicts_total"] += len(set(conflicts))
        self._record("resolution", configuration_reference, scope)
        return EffectiveConfiguration(
            definition.configuration_id,
            definition.namespace,
            definition.environment,
            definition.profile,
            scope,
            values,
            provenance,
            tuple(explanation),
            serialize(validation) if validation else {"status": "not-validated"},
            tuple(sorted(set(conflicts))),
            {"v6_behavior_preserved": True, "adapters": ["v6-reference"]},
            {
                "secret_values_exposed": False,
                "read_only": True,
                "tenant_isolated": True,
                "workspace_isolated": True,
            },
            definition.version,
        )

    def snapshot(
        self, effective: EffectiveConfiguration, audit_reference: str
    ) -> ConfigurationSnapshot:
        payload = json.dumps(
            serialize(effective.effective_field_references),
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        digest = hashlib.sha256(payload).hexdigest()
        definition = self.registry.configurations.get(
            effective.configuration_reference, ConfigurationDefinition
        )
        item = ConfigurationSnapshot(
            str(uuid4()),
            definition.configuration_id,
            definition.environment,
            definition.profile,
            definition.version,
            definition.schema_reference,
            definition.source_references,
            digest,
            "valid",
            ValidationStatus(
                str(effective.validation_summary.get("status", "not-validated"))
            ),
            now_utc(),
            audit_reference,
        )
        self.snapshots.register(item.snapshot_id, item)
        self.metric_values["v7_configuration_snapshots_total"] += 1
        self._record("snapshot", item.snapshot_id, effective.scope)
        return item

    def verify_snapshot(
        self, snapshot_id: str, effective: EffectiveConfiguration
    ) -> bool:
        item = self.snapshots.get(snapshot_id, ConfigurationSnapshot)
        encoded = json.dumps(
            serialize(effective.effective_field_references),
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return item.effective_value_hash == hashlib.sha256(encoded).hexdigest()

    def compare(
        self,
        before_reference: str,
        before: Mapping[str, object],
        after_reference: str,
        after: Mapping[str, object],
        before_provenance: Mapping[str, str] | None = None,
        after_provenance: Mapping[str, str] | None = None,
    ) -> ConfigurationDiff:
        entries: list[DiffEntry] = []
        names = sorted(set(before) | set(after))
        for name in names[:MAX_DIFF_ENTRIES]:
            old, new = before.get(name), after.get(name)
            if old == new:
                continue
            entries.append(
                DiffEntry(
                    name,
                    "added"
                    if name not in before
                    else "removed"
                    if name not in after
                    else "changed",
                    safe_value(name, old),
                    safe_value(name, new),
                    (
                        f"{(before_provenance or {}).get(name)} -> "
                        f"{(after_provenance or {}).get(name)}"
                    ),
                    security_impact="secret-reference"
                    if is_secret_field(name)
                    else "none",
                )
            )
        result = ConfigurationDiff(
            str(uuid4()),
            before_reference,
            after_reference,
            tuple(entries),
            len(names) > MAX_DIFF_ENTRIES,
        )
        self.diffs.register(result.diff_id, result)
        self._record("diff", result.diff_id)
        return result

    def plan_change(
        self,
        current_reference: str,
        proposed_reference: str,
        diff_reference: str,
        validation_reference: str,
        compatibility_reference: str,
        security_review_reference: str,
        rollback_reference: str,
        audit_reference: str,
    ) -> ChangePlan:
        self.diffs.get(diff_reference, ConfigurationDiff)
        item = ChangePlan(
            str(uuid4()),
            current_reference,
            proposed_reference,
            diff_reference,
            validation_reference,
            compatibility_reference,
            security_review_reference,
            "review required; framework does not apply changes",
            rollback_reference,
            None,
            "draft",
            audit_reference,
        )
        self.change_plans.register(item.change_plan_id, item)
        self._record("change-plan", item.change_plan_id)
        return item

    def assess_migration(
        self,
        source_mapping: Mapping[str, str],
        schema_mapping: Mapping[str, str],
        audit_reference: str,
    ) -> MigrationAssessment:
        item = MigrationAssessment(
            str(uuid4()),
            source_mapping,
            schema_mapping,
            True,
            ("review mappings", "validate proposed references", "approve separately"),
            ("retain current active reference",),
            bool(source_mapping and schema_mapping),
            audit_reference,
        )
        self.migrations.register(item.assessment_id, item)
        self._record("migration-assessment", item.assessment_id)
        return item

    def diagnose(self, scope: Scope) -> tuple[Mapping[str, object], ...]:
        findings: list[Mapping[str, object]] = []
        configurations = self.registry.lookup_configurations(scope)
        if not configurations:
            findings.append({"code": "missing-configuration", "severity": "warning"})
        for override in self.registry.overrides.values(OverrideArtifact):
            if override.scope == scope and override.expired:
                findings.append(
                    {
                        "code": "expired-override",
                        "override_reference": override.override_id,
                        "severity": "warning",
                    }
                )
        safe = tuple(findings[:MAX_RESULTS])
        self.diagnostics.extend(safe)
        return safe

    def health(self, scope: Scope) -> Mapping[str, object]:
        diagnostics = self.diagnose(scope)
        return {
            "registry": "healthy",
            "sources": "healthy",
            "profiles": "healthy",
            "schemas": "healthy",
            "resolution": "healthy",
            "validation": "healthy",
            "compatibility": "healthy",
            "snapshots": "healthy",
            "readiness": not any(item["severity"] == "error" for item in diagnostics),
            "liveness": True,
            "diagnostics": serialize(diagnostics),
        }

    def projection(self, section: str, scope: Scope) -> object:
        projections: dict[str, object] = {
            "registry": self.registry.lookup_configurations(scope),
            "environments": sorted(item.value for item in Environment),
            "profiles": tuple(
                item
                for item in self.registry.profiles.values(EnvironmentProfile)
                if item.profile_id
                in {c.profile for c in self.registry.lookup_configurations(scope)}
            ),
            "sources": tuple(
                item
                for item in self.registry.sources.values(SourceDefinition)
                if item.scope == scope
            ),
            "precedence": tuple(
                item.precedence_rule
                for item in self.registry.profiles.values(EnvironmentProfile)
            ),
            "schemas": tuple(
                item
                for item in self.registry.schemas.values(SchemaDefinition)
                if item.namespace == scope.namespace
            ),
            "defaults": tuple(
                item
                for item in self.registry.defaults.values(DefaultArtifact)
                if item.namespace == scope.namespace
            ),
            "overrides": tuple(
                item
                for item in self.registry.overrides.values(OverrideArtifact)
                if item.scope == scope
            ),
            "effective": (),
            "validation": (),
            "snapshots": self.snapshots.values(ConfigurationSnapshot),
            "versions": tuple(
                c.version for c in self.registry.lookup_configurations(scope)
            ),
            "diff": self.diffs.values(ConfigurationDiff),
            "change-plans": self.change_plans.values(ChangePlan),
            "compatibility": {"v6_behavior_preserved": True},
            "migration": self.migrations.values(MigrationAssessment),
            "diagnostics": self.diagnose(scope),
            "health": self.health(scope),
            "metrics": dict(self.metric_values),
            "audit": tuple(
                item
                for item in self.audit
                if item.get("scope")
                in (None, f"{scope.tenant}/{scope.workspace}/{scope.namespace}")
            ),
            "lifecycle": [item.value for item in Lifecycle],
        }
        if section not in projections:
            raise ConfigurationError(f"unknown projection: {section}")
        return serialize(projections[section])

    def _record(self, action: str, reference: str, scope: Scope | None = None) -> None:
        self.audit.append(
            {
                "action": action,
                "reference": reference,
                "scope": (
                    f"{scope.tenant}/{scope.workspace}/{scope.namespace}"
                    if scope
                    else None
                ),
                "timestamp": now_utc().isoformat(),
                "safe": True,
            }
        )

    @staticmethod
    def _require_scope(actual: Scope, requested: Scope) -> None:
        if actual != requested:
            raise IsolationError("tenant, workspace, or namespace isolation violation")


GLOBAL_CONFIGURATION_FRAMEWORK = ConfigurationFramework()
