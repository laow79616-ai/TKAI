"""Approval-gated continuous optimization over existing bounded interfaces."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from .adapters import (
    BoundedTestDouble,
    ChangeApplicationPort,
    ReadOnlySignalPort,
    ReferenceIntegrityPort,
)
from .metrics import OptimizationMetrics
from .models import (
    Approval,
    AuditEvent,
    Baseline,
    CandidateChange,
    ChangeRecord,
    Evaluation,
    Experiment,
    OptimizationProfile,
    OptimizationStatus,
    Recommendation,
    RequestScope,
    RollbackRecord,
    Signal,
    ValidationResult,
    utcnow,
)

TRANSITIONS: dict[OptimizationStatus, frozenset[OptimizationStatus]] = {
    OptimizationStatus.DRAFT: frozenset(
        {OptimizationStatus.COLLECTING, OptimizationStatus.ARCHIVED}
    ),
    OptimizationStatus.COLLECTING: frozenset(
        {OptimizationStatus.ANALYZING, OptimizationStatus.FAILED}
    ),
    OptimizationStatus.ANALYZING: frozenset(
        {OptimizationStatus.PROPOSED, OptimizationStatus.FAILED}
    ),
    OptimizationStatus.PROPOSED: frozenset(
        {OptimizationStatus.PENDING_REVIEW, OptimizationStatus.ARCHIVED}
    ),
    OptimizationStatus.PENDING_REVIEW: frozenset(
        {OptimizationStatus.APPROVED, OptimizationStatus.REJECTED}
    ),
    OptimizationStatus.APPROVED: frozenset(
        {OptimizationStatus.APPLYING, OptimizationStatus.ARCHIVED}
    ),
    OptimizationStatus.APPLYING: frozenset(
        {OptimizationStatus.VALIDATING, OptimizationStatus.FAILED}
    ),
    OptimizationStatus.VALIDATING: frozenset(
        {
            OptimizationStatus.COMPLETED,
            OptimizationStatus.ROLLED_BACK,
            OptimizationStatus.FAILED,
        }
    ),
    OptimizationStatus.COMPLETED: frozenset({OptimizationStatus.ARCHIVED}),
    OptimizationStatus.REJECTED: frozenset({OptimizationStatus.ARCHIVED}),
    OptimizationStatus.ROLLED_BACK: frozenset({OptimizationStatus.ARCHIVED}),
    OptimizationStatus.FAILED: frozenset(
        {OptimizationStatus.ROLLED_BACK, OptimizationStatus.ARCHIVED}
    ),
    OptimizationStatus.ARCHIVED: frozenset({OptimizationStatus.DELETED}),
    OptimizationStatus.DELETED: frozenset(),
}


class TikTokAIContinuousOptimizationCenter:
    """Produces advisory recommendations and applies only approved bounded changes."""

    def __init__(
        self,
        signals: ReadOnlySignalPort | None = None,
        changes: ChangeApplicationPort | None = None,
        integrity: ReferenceIntegrityPort | None = None,
    ) -> None:
        adapter = BoundedTestDouble()
        self.signal_port = signals or adapter
        self.change_port = changes or adapter
        self.integrity_port = integrity or adapter
        self.profiles: dict[str, OptimizationProfile] = {}
        self.objectives: dict[str, Any] = {}
        self.baselines: dict[str, Baseline] = {}
        self.signals: dict[str, Signal] = {}
        self.candidates: dict[str, CandidateChange] = {}
        self.experiments: dict[str, Experiment] = {}
        self.simulations: dict[str, Experiment] = {}
        self.evaluations: dict[str, Evaluation] = {}
        self.recommendations: dict[str, Recommendation] = {}
        self.approvals: dict[str, Approval] = {}
        self.changes: dict[str, ChangeRecord] = {}
        self.validations: dict[str, ValidationResult] = {}
        self.rollbacks: dict[str, RollbackRecord] = {}
        self.audit: list[AuditEvent] = []
        self.profile_versions: list[dict[str, Any]] = []
        self.metrics = OptimizationMetrics()

    @staticmethod
    def _require(scope: RequestScope, action: str) -> None:
        permission = f"tiktok:optimization:{action}"
        if (
            permission not in scope.permissions
            and "tiktok:optimization:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(item: Any, scope: RequestScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def scoped_values(self, values: Any, scope: RequestScope) -> list[Any]:
        self._require(scope, "read")
        return [
            item
            for item in values
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def _record(
        self,
        profile: OptimizationProfile,
        scope: RequestScope,
        action: str,
        detail: str = "",
    ) -> None:
        if any(
            marker in detail.casefold()
            for marker in ("password=", "secret=", "token=", "cookie=", "session=")
        ):
            raise ValueError("Secrets are forbidden in optimization audit records.")
        self.audit.append(
            AuditEvent(
                profile.id,
                profile.tenant,
                profile.workspace,
                scope.actor,
                action,
                detail,
            )
        )

    def create_profile(
        self, profile: OptimizationProfile, scope: RequestScope
    ) -> OptimizationProfile:
        self._require(scope, "write")
        self._scoped(profile, scope)
        profile.validate()
        if profile.id in self.profiles:
            raise ValueError("Optimization profile ID must be unique.")
        self.profiles[profile.id] = profile
        self.profile_versions.append(profile.to_dict())
        self.metrics.increment("tiktok_optimization_profiles_total")
        self._record(profile, scope, "profile.created")
        return profile

    def transition(
        self, profile_id: str, status: OptimizationStatus, scope: RequestScope
    ) -> OptimizationProfile:
        self._require(scope, "write")
        profile = self.profiles[profile_id]
        self._scoped(profile, scope)
        if status not in TRANSITIONS[profile.status]:
            raise ValueError(
                "Invalid optimization transition: "
                f"{profile.status.value} -> {status.value}"
            )
        profile.status = status
        profile.version += 1
        profile.updated_at = utcnow()
        self.profile_versions.append(profile.to_dict())
        self._record(profile, scope, f"profile.transition.{status.value}")
        return profile

    def capture_baseline(self, baseline: Baseline, scope: RequestScope) -> Baseline:
        self._require(scope, "analyze")
        profile = self.profiles[baseline.profile_id]
        self._scoped(profile, scope)
        self._scoped(baseline, scope)
        snapshot = self.signal_port.snapshot(profile.scope.value, scope)
        baseline.metrics.update(
            {
                key: float(value)
                for key, value in snapshot.items()
                if isinstance(value, (int, float))
            }
        )
        self.baselines[baseline.id] = baseline
        self._record(profile, scope, "baseline.captured", baseline.id)
        return baseline

    def add_signal(self, signal: Signal, scope: RequestScope) -> Signal:
        self._require(scope, "analyze")
        self._scoped(signal, scope)
        if not signal.evidence_references:
            raise ValueError("Signals require evidence references.")
        self.signals[signal.id] = signal
        return signal

    def add_candidate(
        self, candidate: CandidateChange, scope: RequestScope
    ) -> CandidateChange:
        self._require(scope, "analyze")
        self._scoped(candidate, scope)
        candidate.validate()
        self.candidates[candidate.id] = candidate
        self.metrics.increment("tiktok_optimization_candidates_total")
        return candidate

    def record_experiment(
        self, experiment: Experiment, scope: RequestScope
    ) -> Experiment:
        self._require(scope, "analyze")
        self._scoped(experiment, scope)
        if experiment.kind.value == "canary_configuration":
            raise PermissionError(
                "Canary configuration is an interface only and requires approval."
            )
        self.experiments[experiment.id] = experiment
        if experiment.kind.value == "simulation":
            self.simulations[experiment.id] = experiment
        self.metrics.increment("tiktok_optimization_experiments_total")
        if experiment.regression_detected:
            self.metrics.increment("tiktok_optimization_regressions_total")
        return experiment

    def evaluate(self, evaluation: Evaluation, scope: RequestScope) -> Evaluation:
        self._require(scope, "analyze")
        self._scoped(evaluation, scope)
        if not 0 <= evaluation.confidence <= 1:
            raise ValueError("Confidence must be within [0, 1].")
        if not evaluation.rollback_criteria:
            raise ValueError("Rollback criteria are required.")
        self.evaluations[evaluation.id] = evaluation
        self.metrics.set("tiktok_optimization_confidence", evaluation.confidence)
        return evaluation

    def recommend(
        self, recommendation: Recommendation, scope: RequestScope
    ) -> Recommendation:
        started = perf_counter()
        self._require(scope, "analyze")
        self._scoped(recommendation, scope)
        candidate = self.candidates[recommendation.candidate_id]
        candidate.validate()
        if recommendation.approved:
            raise ValueError("Recommendations must be advisory when created.")
        if not all((recommendation.validation_plan, recommendation.rollback_plan)):
            raise ValueError("Validation and rollback plans are required.")
        self.recommendations[recommendation.id] = recommendation
        self.metrics.increment("tiktok_optimization_recommendations_total")
        self.metrics.set(
            "tiktok_optimization_analysis_seconds", perf_counter() - started
        )
        return recommendation

    def decide(
        self, approval: Approval, profile_id: str, scope: RequestScope
    ) -> Approval:
        self._require(scope, "approve")
        profile = self.profiles[profile_id]
        self._scoped(profile, scope)
        self._scoped(approval, scope)
        if approval.expires_at <= datetime.now(timezone.utc):
            raise ValueError("Approval is already expired.")
        recommendation = self.recommendations[approval.recommendation_id]
        if not approval.approved and not approval.rejection_reason:
            raise ValueError("Rejected approvals require a rejection reason.")
        recommendation.approved = approval.approved
        self.approvals[approval.id] = approval
        self.metrics.increment("tiktok_optimization_approvals_total")
        self._record(
            profile,
            scope,
            "recommendation.approved"
            if approval.approved
            else "recommendation.rejected",
        )
        return approval

    def apply_change(
        self, change: ChangeRecord, profile_id: str, scope: RequestScope
    ) -> ChangeRecord:
        self._require(scope, "apply")
        profile = self.profiles[profile_id]
        self._scoped(profile, scope)
        self._scoped(change, scope)
        recommendation = self.recommendations[change.recommendation_id]
        approvals = [
            item
            for item in self.approvals.values()
            if item.recommendation_id == recommendation.id
            and item.approved
            and item.expires_at > datetime.now(timezone.utc)
        ]
        if not recommendation.approved or not approvals:
            raise PermissionError("A current human approval is required.")
        candidate = self.candidates[recommendation.candidate_id]
        if not self.integrity_port.validate_backup(change.backup_reference, scope):
            raise ValueError("A valid backup reference is required.")
        if not self.integrity_port.validate_checkpoint(
            change.checkpoint_reference, scope
        ):
            raise ValueError("A valid checkpoint reference is required.")
        if not self.change_port.preconditions(
            candidate, change.expected_version, scope
        ):
            raise ValueError("Configuration version validation failed.")
        self.transition(profile.id, OptimizationStatus.APPLYING, scope)
        change.result_reference = self.change_port.apply(candidate, scope)
        change.applied_at = utcnow()
        self.changes[change.id] = change
        self.metrics.increment("tiktok_optimization_changes_total")
        self.transition(profile.id, OptimizationStatus.VALIDATING, scope)
        self._record(profile, scope, "change.delegated", change.id)
        return change

    def validate_change(
        self, result: ValidationResult, profile_id: str, scope: RequestScope
    ) -> ValidationResult:
        started = perf_counter()
        self._require(scope, "apply")
        profile = self.profiles[profile_id]
        self._scoped(profile, scope)
        self._scoped(result, scope)
        self.validations[result.id] = result
        self.metrics.set(
            "tiktok_optimization_improvement_ratio", result.performance_delta
        )
        if result.regression_detected or not result.accepted:
            self.metrics.increment("tiktok_optimization_regressions_total")
            self.rollback(
                result.change_id, profile_id, scope, "automatic regression", True
            )
        else:
            self.transition(profile_id, OptimizationStatus.COMPLETED, scope)
            self.metrics.increment("tiktok_optimization_success_total")
        self.metrics.set(
            "tiktok_optimization_validation_seconds", perf_counter() - started
        )
        return result

    def rollback(
        self,
        change_id: str,
        profile_id: str,
        scope: RequestScope,
        reason: str,
        automatic: bool = False,
    ) -> RollbackRecord:
        self._require(scope, "rollback")
        profile = self.profiles[profile_id]
        self._scoped(profile, scope)
        change = self.changes[change_id]
        candidate = self.candidates[
            self.recommendations[change.recommendation_id].candidate_id
        ]
        reference = self.change_port.rollback(
            candidate, change.checkpoint_reference, scope
        )
        record = RollbackRecord(
            f"rollback-{change.id}",
            change.id,
            change.tenant,
            change.workspace,
            reason,
            reference,
            automatic,
            True,
        )
        self.rollbacks[record.id] = record
        self.transition(profile.id, OptimizationStatus.ROLLED_BACK, scope)
        self.metrics.increment("tiktok_optimization_rollbacks_total")
        self._record(profile, scope, "change.rolled_back", reason)
        return record

    def analytics(self, scope: RequestScope) -> dict[str, float]:
        recommendations = self.scoped_values(self.recommendations.values(), scope)
        changes = self.scoped_values(self.changes.values(), scope)
        rollbacks = self.scoped_values(self.rollbacks.values(), scope)
        validations = self.scoped_values(self.validations.values(), scope)
        accepted = sum(item.accepted for item in validations)
        return {
            "optimization_profiles": float(
                len(self.scoped_values(self.profiles.values(), scope))
            ),
            "candidates_generated": float(
                len(self.scoped_values(self.candidates.values(), scope))
            ),
            "recommendations_generated": float(len(recommendations)),
            "recommendations_approved": float(
                sum(item.approved for item in recommendations)
            ),
            "changes_applied": float(len(changes)),
            "rollbacks": float(len(rollbacks)),
            "success_rate": accepted / len(validations) if validations else 0.0,
            "regression_rate": sum(item.regression_detected for item in validations)
            / len(validations)
            if validations
            else 0.0,
            "average_improvement": sum(item.performance_delta for item in validations)
            / len(validations)
            if validations
            else 0.0,
        }

    def dashboard(self, scope: RequestScope) -> dict[str, Any]:
        names = (
            "profiles",
            "objectives",
            "baselines",
            "signals",
            "candidates",
            "experiments",
            "simulations",
            "evaluations",
            "recommendations",
            "approvals",
            "changes",
            "validations",
            "rollbacks",
        )
        return {
            "sections": [
                "Optimization Overview",
                "Profiles",
                "Objectives",
                "Baselines",
                "Signals",
                "Candidates",
                "Experiments",
                "Simulations",
                "Evaluations",
                "Recommendations",
                "Approvals",
                "Changes",
                "Validation",
                "Rollbacks",
                "History",
                "Analytics",
            ],
            "optimization_overview": {
                name: len(self.scoped_values(getattr(self, name).values(), scope))
                for name in names
            },
            "analytics": self.analytics(scope),
        }

    def history(self, scope: RequestScope) -> dict[str, Any]:
        return {
            "profile_versions": [
                item
                for item in self.profile_versions
                if item["tenant"] == scope.tenant
                and item["workspace"] == scope.workspace
            ],
            "audit_trail": [
                asdict(item) for item in self.scoped_values(self.audit, scope)
            ],
        }
