"""Tenant-isolated, bounded risk evaluation and coordination."""

from __future__ import annotations

from dataclasses import asdict
from datetime import timedelta
from time import perf_counter
from typing import Any

from .adapters import NullRiskControlPort, RiskControlPort
from .metrics import RiskMetrics
from .models import (
    Alert,
    AlertStatus,
    HealthStatus,
    Lifecycle,
    Pause,
    RecoveryRecord,
    Restriction,
    ReviewDecision,
    RiskAction,
    RiskLevel,
    RiskLimit,
    RiskPolicy,
    RiskProfile,
    RiskReview,
    RiskRule,
    RiskScope,
    RiskScore,
    RiskSignal,
    RuleOperator,
    utcnow,
)


class TikTokRiskControlCenter:
    """Safety control plane; it never bypasses a platform restriction or challenge."""

    def __init__(
        self,
        *,
        accounts: RiskControlPort | None = None,
        browsers: RiskControlPort | None = None,
        proxies: RiskControlPort | None = None,
        workflows: RiskControlPort | None = None,
        publishing: RiskControlPort | None = None,
        interaction: RiskControlPort | None = None,
        collection: RiskControlPort | None = None,
        thresholds: dict[RiskLevel, float] | None = None,
    ) -> None:
        self.ports = {
            "account": accounts or NullRiskControlPort(),
            "browser": browsers or NullRiskControlPort(),
            "proxy": proxies or NullRiskControlPort(),
            "workflow": workflows or NullRiskControlPort(),
            "publishing": publishing or NullRiskControlPort(),
            "interaction": interaction or NullRiskControlPort(),
            "collection": collection or NullRiskControlPort(),
        }
        self.thresholds = thresholds or {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 30,
            RiskLevel.HIGH: 60,
            RiskLevel.CRITICAL: 85,
        }
        values = list(self.thresholds.values())
        if (
            set(self.thresholds) != set(RiskLevel)
            or values != sorted(values)
            or any(not 0 <= v <= 100 for v in values)
        ):
            raise ValueError(
                "Risk thresholds must cover every level, be ordered, "
                "and stay within [0, 100]."
            )
        self.profiles: dict[str, RiskProfile] = {}
        self.policies: dict[str, RiskPolicy] = {}
        self.rules: dict[str, RiskRule] = {}
        self.signals: dict[str, RiskSignal] = {}
        self.scores: dict[str, list[RiskScore]] = {}
        self.events: list[dict[str, Any]] = []
        self.alerts: dict[str, Alert] = {}
        self.restrictions: dict[str, Restriction] = {}
        self.limits: dict[str, RiskLimit] = {}
        self.pauses: dict[str, Pause] = {}
        self.reviews: dict[str, RiskReview] = {}
        self.recoveries: dict[str, RecoveryRecord] = {}
        self.health: dict[str, HealthStatus] = {}
        self.audit: list[dict[str, str]] = []
        self.metrics = RiskMetrics()

    @staticmethod
    def _require(scope: RiskScope, action: str) -> None:
        permission = f"tiktok:risk:{action}"
        if (
            permission not in scope.permissions
            and "tiktok:risk:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(item: Any, scope: RiskScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _audit(self, action: str, resource: str, scope: RiskScope) -> None:
        self.audit.append(
            {
                "action": action,
                "resource": resource,
                "actor": scope.actor,
                "tenant": scope.tenant,
                "workspace": scope.workspace,
                "occurred_at": utcnow().isoformat(),
            }
        )

    def create_profile(self, profile: RiskProfile, scope: RiskScope) -> RiskProfile:
        self._require(scope, "write")
        self._scoped(profile, scope)
        profile.validate()
        if profile.id in self.profiles:
            raise ValueError("Profile ID must be unique.")
        self.profiles[profile.id] = profile
        self.metrics.increment("tiktok_risk_profiles_total")
        self._audit("profile.create", profile.id, scope)
        return profile

    def list_profiles(self, scope: RiskScope) -> list[RiskProfile]:
        self._require(scope, "read")
        return [
            p
            for p in self.profiles.values()
            if p.tenant == scope.tenant
            and p.workspace == scope.workspace
            and p.status is not Lifecycle.DELETED
        ]

    def transition_profile(
        self, reference: str, status: Lifecycle, scope: RiskScope
    ) -> RiskProfile:
        self._require(scope, "write")
        profile = self.profiles[reference]
        self._scoped(profile, scope)
        allowed = {
            Lifecycle.DRAFT: {Lifecycle.ACTIVE, Lifecycle.ARCHIVED, Lifecycle.DELETED},
            Lifecycle.ACTIVE: {
                Lifecycle.MONITORING,
                Lifecycle.REVIEW_REQUIRED,
                Lifecycle.PAUSED,
            },
            Lifecycle.MONITORING: {
                Lifecycle.REVIEW_REQUIRED,
                Lifecycle.PAUSED,
                Lifecycle.RESOLVED,
            },
            Lifecycle.REVIEW_REQUIRED: {
                Lifecycle.ACTIVE,
                Lifecycle.PAUSED,
                Lifecycle.RESOLVED,
            },
            Lifecycle.PAUSED: {Lifecycle.RECOVERING, Lifecycle.RESOLVED},
            Lifecycle.RECOVERING: {Lifecycle.PAUSED, Lifecycle.RESOLVED},
            Lifecycle.RESOLVED: {Lifecycle.MONITORING, Lifecycle.ARCHIVED},
            Lifecycle.ARCHIVED: {Lifecycle.DRAFT, Lifecycle.DELETED},
            Lifecycle.DELETED: set(),
        }
        if status not in allowed[profile.status]:
            raise ValueError(
                f"Invalid risk transition: {profile.status.value} -> {status.value}"
            )
        profile.status, profile.version, profile.updated_at = (
            status,
            profile.version + 1,
            utcnow(),
        )
        self._audit(f"profile.{status.value}", reference, scope)
        return profile

    def create_policy(self, policy: RiskPolicy, scope: RiskScope) -> RiskPolicy:
        self._require(scope, "policy")
        self._scoped(policy, scope)
        policy.validate()
        self.policies[policy.id] = policy
        self._audit("policy.create", policy.id, scope)
        return policy

    def create_rule(self, rule: RiskRule, scope: RiskScope) -> RiskRule:
        self._require(scope, "policy")
        self._scoped(rule, scope)
        rule.validate()
        policy = self.policies[rule.policy_reference]
        self._scoped(policy, scope)
        self.rules[rule.id] = rule
        self._audit("rule.create", rule.id, scope)
        return rule

    def set_limit(self, limit: RiskLimit, scope: RiskScope) -> RiskLimit:
        self._require(scope, "policy")
        self._scoped(limit, scope)
        limit.validate()
        self.limits[limit.id] = limit
        self._audit("limit.set", limit.id, scope)
        return limit

    def ingest_signal(self, signal: RiskSignal, scope: RiskScope) -> RiskSignal:
        self._require(scope, "signal")
        self._scoped(signal, scope)
        signal.validate()
        if signal.id in self.signals:
            raise ValueError("Signal ID must be unique.")
        self.signals[signal.id] = signal
        self.events.append(
            {
                "kind": "signal",
                "reference": signal.id,
                "tenant": signal.tenant,
                "workspace": signal.workspace,
                "occurred_at": signal.occurred_at.isoformat(),
            }
        )
        self.metrics.increment("tiktok_risk_events_total")
        self._audit("signal.ingest", signal.id, scope)
        return signal

    def evaluate(self, profile_reference: str, scope: RiskScope) -> RiskScore:
        started = perf_counter()
        self._require(scope, "evaluate")
        profile = self.profiles[profile_reference]
        self._scoped(profile, scope)
        relevant = [
            s
            for s in self.signals.values()
            if s.tenant == scope.tenant
            and s.workspace == scope.workspace
            and (
                not s.account_reference
                or s.account_reference == profile.account_reference
            )
        ]
        now = utcnow()
        contributions = []
        explanation = []
        matched: list[RiskRule] = []
        for signal in relevant:
            age_hours = max(0, (now - signal.occurred_at).total_seconds() / 3600)
            recency = 1 / (1 + age_hours / 24)
            value = signal.severity * 10 * signal.confidence * recency
            contributions.append(value)
            explanation.append(
                f"{signal.kind.value}: severity={signal.severity}, "
                f"confidence={signal.confidence:.2f}, recency={recency:.2f}"
            )
        score_value = min(
            100.0,
            sum(contributions) / max(1, len(contributions))
            + min(20, len(relevant) * 2),
        )
        for rule in sorted(
            self.rules.values(), key=lambda item: item.priority, reverse=True
        ):
            if (
                not rule.enabled
                or rule.tenant != scope.tenant
                or rule.workspace != scope.workspace
            ):
                continue
            window_start = now - timedelta(seconds=rule.window_seconds)
            window = [
                s
                for s in relevant
                if s.occurred_at >= window_start
                and (rule.signal_kind is None or s.kind is rule.signal_kind)
            ]
            is_match = (
                (rule.operator is RuleOperator.SIGNAL_MATCH and bool(window))
                or (
                    rule.operator is RuleOperator.THRESHOLD_MATCH
                    and score_value >= rule.threshold
                )
                or (
                    rule.operator is RuleOperator.TREND_MATCH
                    and len(window) >= rule.trend_count
                )
            )
            if is_match:
                matched.append(rule)
        level = max(
            (
                level
                for level, threshold in self.thresholds.items()
                if score_value >= threshold
            ),
            key=lambda level: self.thresholds[level],
        )
        recommended = (
            matched[0].action
            if matched
            else (
                RiskAction.NOTIFY
                if level in {RiskLevel.LOW, RiskLevel.MEDIUM}
                else RiskAction.REQUIRE_REVIEW
            )
        )
        score = RiskScore(
            profile_reference,
            round(score_value, 2),
            level,
            tuple(explanation) or ("No active risk signals.",),
            recommended,
        )
        self.scores.setdefault(profile_reference, []).append(score)
        profile.risk_score, profile.risk_level, profile.updated_at = (
            score.score,
            score.level,
            now,
        )
        self.metrics.set("tiktok_risk_score", score.score)
        self.metrics.set(
            "tiktok_risk_evaluation_latency_seconds", perf_counter() - started
        )
        for rule in matched:
            self.execute_action(rule.action, profile, scope, rule.id)
        self._audit("score.evaluate", profile_reference, scope)
        return score

    def execute_action(
        self,
        action: RiskAction,
        profile: RiskProfile,
        scope: RiskScope,
        rule_reference: str = "",
        approval_reference: str = "",
    ) -> None:
        self._require(scope, "action")
        self._scoped(profile, scope)
        destructive = {
            RiskAction.PAUSE_ACCOUNT,
            RiskAction.PAUSE_WORKFLOW,
            RiskAction.PAUSE_PUBLISHING,
            RiskAction.PAUSE_INTERACTION,
            RiskAction.PAUSE_COLLECTION,
            RiskAction.DRAIN_BROWSER,
            RiskAction.RELEASE_PROXY,
            RiskAction.KILL_SWITCH,
        }
        if action in destructive and action is not RiskAction.KILL_SWITCH:
            if approval_reference:
                review = self.reviews[approval_reference]
                self._scoped(review, scope)
                if review.decision is not ReviewDecision.APPROVED:
                    raise PermissionError("Approved risk review required.")
            elif profile.risk_level is not RiskLevel.CRITICAL:
                raise PermissionError(
                    "Approval is required for non-critical control actions."
                )
        target = profile.account_reference or profile.id
        mapping = {
            RiskAction.PAUSE_ACCOUNT: ("account", "pause"),
            RiskAction.PAUSE_WORKFLOW: ("workflow", "pause"),
            RiskAction.PAUSE_PUBLISHING: ("publishing", "pause"),
            RiskAction.PAUSE_INTERACTION: ("interaction", "pause"),
            RiskAction.PAUSE_COLLECTION: ("collection", "pause"),
            RiskAction.DRAIN_BROWSER: ("browser", "drain"),
            RiskAction.RELEASE_PROXY: ("proxy", "release"),
        }
        if action in mapping:
            port, operation = mapping[action]
            self.ports[port].apply(operation, target, f"risk rule {rule_reference}")
            pause = Pause(
                f"pause-{len(self.pauses) + 1}",
                scope.tenant,
                scope.workspace,
                port,
                target,
                f"risk rule {rule_reference}",
                False,
            )
            self.pauses[pause.id] = pause
            metric = (
                "tiktok_risk_workspaces_paused_total"
                if port == "workflow"
                else "tiktok_risk_accounts_paused_total"
            )
            self.metrics.increment(metric)
        alert = Alert(
            f"alert-{len(self.alerts) + 1}",
            scope.tenant,
            scope.workspace,
            profile.risk_level,
            "risk-control",
            f"{action.value} recommended for {profile.id}",
            profile.account_reference,
            rule_reference,
        )
        self.alerts[alert.id] = alert
        self.metrics.increment("tiktok_risk_alerts_total")
        self._audit(f"action.{action.value}", profile.id, scope)

    def add_restriction(
        self, restriction: Restriction, scope: RiskScope
    ) -> Restriction:
        self._require(scope, "action")
        self._scoped(restriction, scope)
        self.restrictions[restriction.id] = restriction
        self.metrics.increment("tiktok_risk_restrictions_total")
        self._audit("restriction.add", restriction.id, scope)
        return restriction

    def create_review(self, review: RiskReview, scope: RiskScope) -> RiskReview:
        self._require(scope, "review")
        self._scoped(review, scope)
        self.reviews[review.id] = review
        self._audit("review.create", review.id, scope)
        return review

    def decide_review(
        self, reference: str, decision: ReviewDecision, notes: str, scope: RiskScope
    ) -> RiskReview:
        self._require(scope, "approve")
        review = self.reviews[reference]
        self._scoped(review, scope)
        if decision not in {ReviewDecision.APPROVED, ReviewDecision.REJECTED}:
            raise ValueError("Review decision must approve or reject.")
        if review.expires_at and review.expires_at <= utcnow():
            review.decision = ReviewDecision.EXPIRED
            raise ValueError("Risk review has expired.")
        review.decision, review.notes = decision, notes
        self._audit(f"review.{decision.value}", reference, scope)
        return review

    def update_health(self, health: HealthStatus, scope: RiskScope) -> HealthStatus:
        self._require(scope, "signal")
        self._scoped(health, scope)
        health.validate()
        health.composite = round(
            sum(
                (
                    health.account,
                    health.login,
                    health.session,
                    health.browser,
                    health.proxy,
                    health.publishing,
                    health.interaction,
                    health.collection,
                )
            )
            / 8,
            2,
        )
        health.last_check = utcnow()
        self.health[health.id] = health
        self._audit("health.update", health.id, scope)
        return health

    def recover(
        self, recovery: RecoveryRecord, scope: RiskScope, approval_reference: str = ""
    ) -> RecoveryRecord:
        self._require(scope, "recover")
        self._scoped(recovery, scope)
        recovery.validate()
        profile = self.profiles[recovery.profile_reference]
        self._scoped(profile, scope)
        if recovery.unresolved_platform_condition:
            recovery.outcome = "stopped_unresolved_platform_condition"
            self.recoveries[recovery.id] = recovery
            self.metrics.increment("tiktok_risk_recovery_total")
            self._audit("recovery.stopped", recovery.id, scope)
            return recovery
        if not recovery.manual:
            review = self.reviews.get(approval_reference)
            if review is None or review.decision is not ReviewDecision.APPROVED:
                raise PermissionError(
                    "Approved review required for automatic recovery."
                )
        recovery.attempts += 1
        if recovery.attempts > recovery.maximum_attempts:
            recovery.outcome = "maximum_attempts_reached"
        else:
            results = [
                port.recover(profile.account_reference, recovery.checkpoint_reference)
                for port in self.ports.values()
            ]
            recovery.outcome = "succeeded" if all(results) else "failed"
            if recovery.outcome == "succeeded":
                self.metrics.increment("tiktok_risk_recovery_success_total")
        self.recoveries[recovery.id] = recovery
        self.metrics.increment("tiktok_risk_recovery_total")
        self._audit(f"recovery.{recovery.outcome}", recovery.id, scope)
        return recovery

    def acknowledge_alert(self, reference: str, scope: RiskScope) -> Alert:
        self._require(scope, "review")
        alert = self.alerts[reference]
        self._scoped(alert, scope)
        alert.status, alert.acknowledged_by = AlertStatus.ACKNOWLEDGED, scope.actor
        alert.history.append(f"acknowledged:{scope.actor}:{utcnow().isoformat()}")
        return alert

    def analytics(self, scope: RiskScope) -> dict[str, Any]:
        self._require(scope, "read")

        def scoped(values: Any) -> list[Any]:
            return [
                value
                for value in values
                if value.tenant == scope.tenant and value.workspace == scope.workspace
            ]

        profiles, alerts, recoveries = (
            scoped(self.profiles.values()),
            scoped(self.alerts.values()),
            scoped(self.recoveries.values()),
        )
        return {
            "risk_events": len(
                [
                    e
                    for e in self.events
                    if e["tenant"] == scope.tenant and e["workspace"] == scope.workspace
                ]
            ),
            "risk_distribution": {
                level.value: sum(p.risk_level is level for p in profiles)
                for level in RiskLevel
            },
            "accounts_paused": len(scoped(self.pauses.values())),
            "workspaces_paused": sum(
                p.kind == "workflow" for p in scoped(self.pauses.values())
            ),
            "restrictions": len(scoped(self.restrictions.values())),
            "recoveries": len(recoveries),
            "recovery_success_rate": sum(r.outcome == "succeeded" for r in recoveries)
            / max(1, len(recoveries)),
            "alert_volume": len(alerts),
            "trend": [s.score for history in self.scores.values() for s in history][
                -20:
            ],
        }

    def dashboard(self, scope: RiskScope) -> dict[str, Any]:
        return {
            "overview": self.analytics(scope),
            "profiles": [p.to_dict() for p in self.list_profiles(scope)],
            "signals": len(
                [
                    s
                    for s in self.signals.values()
                    if s.tenant == scope.tenant and s.workspace == scope.workspace
                ]
            ),
            "policies": len(
                [
                    p
                    for p in self.policies.values()
                    if p.tenant == scope.tenant and p.workspace == scope.workspace
                ]
            ),
            "rules": len(
                [
                    r
                    for r in self.rules.values()
                    if r.tenant == scope.tenant and r.workspace == scope.workspace
                ]
            ),
            "health": [
                asdict(h)
                for h in self.health.values()
                if h.tenant == scope.tenant and h.workspace == scope.workspace
            ],
        }
