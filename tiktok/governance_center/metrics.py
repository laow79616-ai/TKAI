from collections import defaultdict

METRIC_NAMES = (
    "tiktok_governance_profiles_total",
    "tiktok_governance_policies_total",
    "tiktok_governance_rules_total",
    "tiktok_governance_controls_total",
    "tiktok_governance_approvals_total",
    "tiktok_governance_rejections_total",
    "tiktok_governance_reviews_total",
    "tiktok_governance_exceptions_total",
    "tiktok_governance_changes_total",
    "tiktok_governance_audit_events_total",
    "tiktok_governance_compliance_findings_total",
    "tiktok_governance_safety_events_total",
    "tiktok_governance_approval_seconds",
    "tiktok_governance_review_seconds",
)


class GovernanceMetrics:
    def __init__(self) -> None:
        self.values: defaultdict[str, float] = defaultdict(float)

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown governance metric: {name}")
        self.values[name] += amount

    def observe(self, name: str, value: float) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown governance metric: {name}")
        self.values[name] = max(0, value)

    def render_prometheus(self) -> str:
        return (
            "\n".join(f"# TYPE {n} gauge\n{n} {self.values[n]:g}" for n in METRIC_NAMES)
            + "\n"
        )
