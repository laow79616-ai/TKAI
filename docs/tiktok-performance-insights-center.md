# TikTok Performance Insights Center

## Architecture and lifecycle

The center is a local, single-user, tenant- and workspace-isolated analytical
layer. Profiles move through Draft, Collecting, Analyzing, Ready, Review,
Approved, Archived, and Deleted. Invalid transitions are rejected and every
change is versioned and audited.

## Data, metrics, and dimensions

Datasets use read-only bounded adapters, opaque source/schema references,
encrypted dataset references, bounded time ranges (maximum 366 days), integrity
validation, and result limits (maximum 500). Metrics cover account, browser,
device, proxy, publishing, pipeline, campaign, workflow, automation, execution,
recovery, risk, resource, runtime, queue, review, approval, and growth health.
Custom metrics require an explicit bounded definition. Supported dimensions are
account, workspace, project, campaign, content type, workflow, task/resource
type, browser node, device type, proxy region, status, risk level, and time.

## Analysis and reporting

Versioned benchmarks support historical, workspace, profile, target, previous
period, rolling-average, and percentile references. Comparisons, hourly through
monthly trends, rolling windows, change-point references, anomaly evidence,
bounded advisory forecasts, explainable insights, recommendations, reports, and
integrity-validated snapshots retain their evidence references. No accuracy
claim is made for anomaly or forecast output.

## Integrations

All TikTok control-platform inputs are accessed through the shared read-only
port: Growth, Content Pipeline, Campaign, Creator, Optimization, Decision,
Control Tower, Recovery, Execution, Operations Planner, Automation, Runtime,
Resources, Scheduler, Browser Cluster, Devices, Accounts, Browser Runtime,
Proxy, Workflow, Operations, Risk, Content, Publishing, Collection,
Interaction, Analytics, and Local Runtime. The port exposes no mutation method.

## Security and safety

RBAC, tenant/workspace isolation, safe metadata validation, opaque references,
encrypted dataset references, dataset integrity checks, bounded queries, time
ranges, and result sizes are enforced. Cookies, sessions, credentials, tokens,
and secrets are forbidden in metadata and logs. API routes are GET-only.

Insights and recommendations are advisory. The center cannot execute, publish,
or approve handoffs. Existing approval-gated Optimization and Decision systems
remain the only handoff path. Guidance for CAPTCHA bypass, restriction
circumvention, security bypass, anti-detection guarantees, spam, engagement
manipulation, bulk messaging, or unrestricted mass actions is rejected.

## Operations and Windows local guide

Start the existing local API and dashboard normally. Open
`/tiktok-performance-insights` in the dashboard. Health and inventory are
available at `/tiktok/performance-insights/analytics`; Prometheus text is at
`/tiktok/performance-insights/metrics-exposure`. No live TikTok connection is
required for tests. On Windows PowerShell, activate `.venv`, run the focused
pytest module, then run the repository validation commands from the repository
root.
