"""Prometheus-compatible TikTok metrics."""

from collections import defaultdict

METRICS = (
    "tiktok_accounts_total",
    "tiktok_active_accounts_total",
    "tiktok_login_success_total",
    "tiktok_login_failure_total",
    "tiktok_cookie_expired_total",
    "tiktok_session_expired_total",
    "tiktok_risk_events_total",
)


class TikTokMetrics:
    def __init__(self) -> None:
        self._values: dict[str, float] = defaultdict(float)

    def increment(self, name: str, value: float = 1) -> None:
        if name not in METRICS or value < 0:
            raise ValueError(f"Invalid metric update: {name}")
        self._values[name] += value

    def set(self, name: str, value: float) -> None:
        if name not in METRICS or value < 0:
            raise ValueError(f"Invalid metric value: {name}")
        self._values[name] = value

    def snapshot(self) -> dict[str, float]:
        return {name: self._values[name] for name in METRICS}

    def render_prometheus(self) -> str:
        return "\n".join(f"{name} {value}" for name, value in self.snapshot().items())
