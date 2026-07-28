# TikTok Business Intelligence Center

## Architecture, lifecycle, and scopes
This local single-user module is a tenant/workspace-isolated analytical layer. Existing TikTok modules supply data through `ReadOnlyAnalyticsPort`; the bundled adapter is an offline bounded test double. Workspaces transition through Draft, Collecting, Modeling, Ready, Review, Approved, Archived, and Deleted. Supported business scopes include workspaces, leads, CRM, journeys, campaigns, creators, content, publishing, workflow, automation, execution, operations, resources, risk, growth, performance, and platform.

## Datasets and semantic models
Datasets carry opaque source/schema references, bounded time ranges, freshness, aggregation, version, integrity status, encrypted storage reference, consent awareness, and purpose. Only integrity-valid datasets are queryable. Semantic models define entities, relationships, hierarchies, business definitions, and versions.

## KPIs, metrics, dimensions, and measures
The bounded catalog covers lead, CRM, journey, campaign, content, publishing, workflow, execution, recovery, runtime, resource, risk, and growth KPIs. Metrics use allow-listed aggregations. Dimensions and measures are allow-listed and declarative; arbitrary code is impossible.

## Queries
Queries select registered datasets, KPIs, metrics, dimensions, filters, sorting, pagination, time range, row limit, and timeout. Limits are 500 rows/page, 10,000 total rows, 30 seconds, and 366 days. Raw SQL is never accepted. Sensitive fields are masked and protected attributes rejected.

## Dashboards, reports, comparisons, trends, forecasts, and insights
Versioned artifacts support executive and scoped dashboards/reports, previous/target/workspace/campaign/stage/content/operational comparisons, and hourly through quarterly or rolling trends. Forecasts and insights require confidence and evidence. All output is explainable and advisory.

## Snapshots, exports, history, and governance
Snapshots preserve integrity-validated point-in-time views. Exports generate bounded CSV/JSON; XLSX/PDF remain opaque references to shared exporters. RBAC, row/size limits, and audit are mandatory. History covers every artifact. Governance records ownership, certification, glossary, lineage, classification, access, retention, consent, purpose, and audit.

## Integrations
Customer journey, CRM, lead, business workspace, performance, growth, content, campaign, creator, optimization, decision, control tower, recovery, execution, planning, automation, runtime, resource, scheduling, browser, device, account, proxy, workflow, operations, risk, publishing, collection, interaction, analytics, and local-runtime modules are read only through bounded adapters. Shared metrics, audit, observability, security, export, governance, decision, and reporting infrastructure is reused.

## Privacy, security, and safety
Tenant/workspace isolation and RBAC are mandatory. Metadata rejects secrets and protected attributes. References are opaque or encrypted; cookies, sessions, proxy credentials, and secrets never enter logs. Analytics cannot execute, publish, contact users, send bulk messages, automate spam, bypass CAPTCHA/restrictions/security, or promise anti-detection. Any handoff is approval-gated and honors restrictions, challenges, pauses, and kill switches.

## Operations and Windows local guide
Run `scripts\start-tkai.ps1`, open `tiktok-business-intelligence`, and inspect `/tiktok/business-intelligence/metrics`. Stop with `scripts\stop-tkai.ps1`. Backups, observability, security, audit, OpenAPI, and exports use shared platform facilities.
