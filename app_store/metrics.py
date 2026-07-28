"""Prometheus-compatible Enterprise App Store metrics."""

METRICS = (
    "app_store_applications_total",
    "app_store_publishers_total",
    "app_store_installs_total",
    "app_store_install_failures_total",
    "app_store_updates_total",
    "app_store_active_installations",
    "app_store_reviews_total",
    "app_store_license_validations_total",
)


class AppStoreMetrics:
    def __init__(self) -> None:
        self.values: dict[str, float] = {name: 0 for name in METRICS}

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in self.values:
            raise ValueError("Unknown App Store metric.")
        self.values[name] += amount

    def gauge(self, name: str, value: float) -> None:
        if name not in self.values:
            raise ValueError("Unknown App Store metric.")
        self.values[name] = value

    def snapshot(self) -> dict[str, float]:
        return dict(self.values)

    def render_prometheus(self) -> str:
        return "".join(f"{name} {value}\n" for name, value in self.values.items())
