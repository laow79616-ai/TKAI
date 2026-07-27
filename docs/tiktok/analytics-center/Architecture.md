# TikTok AI Analytics Center Architecture

The analytics center is a tenant- and workspace-isolated reporting plane for the
TikTok Cloud Control Platform. It consumes read-only metric ports from Accounts,
Browsers, Proxies, Farming, Content, Publishing, Collection, Interaction, Risk,
Workflow, and Operations. Shared observability, metrics, dashboard, security, and
audit facilities remain authoritative; this module does not duplicate them.

The domain is separated into reports, dashboards, KPIs, datasets, aggregations,
trends, comparisons, forecasts, history, exports, insights, dashboard, and API
packages. No component calls TikTok directly or implements restriction bypass.
