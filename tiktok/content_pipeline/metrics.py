"""Prometheus metrics for the TikTok Content Pipeline."""

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_content_pipelines_total",
    "tiktok_content_pipeline_jobs_total",
    "tiktok_content_pipeline_running_total",
    "tiktok_content_pipeline_completed_total",
    "tiktok_content_pipeline_failed_total",
    "tiktok_content_pipeline_reviews_total",
    "tiktok_content_pipeline_approvals_total",
    "tiktok_content_pipeline_packages_total",
    "tiktok_content_pipeline_handoffs_total",
    "tiktok_content_pipeline_retries_total",
    "tiktok_content_pipeline_quality_score",
    "tiktok_content_pipeline_processing_seconds",
    "tiktok_content_pipeline_review_seconds",
    "tiktok_content_pipeline_latency_seconds",
)


class PipelineMetrics:
    def __init__(self) -> None:
        self.values: dict[str, float] = defaultdict(float)

    def increment(self, name: str, amount: float = 1) -> None:
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        self.values[name] = value

    def render_prometheus(self) -> str:
        return (
            "\n".join(
                f"# TYPE {name} gauge\n{name} {self.values[name]}"
                for name in METRIC_NAMES
            )
            + "\n"
        )
