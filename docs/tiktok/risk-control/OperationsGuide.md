# Operations Guide

1. Configure ordered Low, Medium, High, and Critical thresholds within 0–100.
2. Create tenant/workspace policies, then add only typed signal, threshold, or trend rules.
3. Feed bounded health and status events from existing TikTok modules through authenticated integration services.
4. Monitor the dashboard, alerts, risk distribution, pauses, and recovery outcomes.
5. Review evidence references before approving state-changing actions or recovery.
6. If a challenge, restriction, suspension, or ban remains unresolved, keep the affected scope paused and use TikTok's supported review process. Do not attempt automated recovery.
7. Use the kill switch only under established incident authority. Audit every acknowledgement, approval, pause, resume, and recovery outcome.

Prometheus metrics are available at `/tiktok/risk-control/metrics`; operational state is available at `/tiktok/risk-control/dashboard`.
