# TikTok AI Control Tower Architecture

The Control Tower is a tenant- and workspace-scoped aggregation layer over existing
TikTok modules. It owns no browser, device, proxy, account, scheduler, runtime,
workflow, automation, execution, publishing, collection, interaction, risk,
analytics, or recovery infrastructure.

Injected read-only providers expose normalized health snapshots. The service builds
overview and topology projections, scoped alerts, activity, and Prometheus metrics.
Missing providers are reported as unavailable instead of being recreated.
