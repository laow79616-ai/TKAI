# Enterprise TikTok Creator Workspace

## Architecture

The Creator Workspace is a local, single-user control plane for creative planning.
It owns workspace organization, project lifecycle, asset references, calendars,
templates, reviews, approvals, audit history, dashboard summaries, and workspace
KPIs. It does not own content storage, publishing execution, analytics collection,
workflow execution, automation execution, decisions, or runtime management.

Bounded ports coordinate the existing TikTok Content Center, Publishing Center,
Analytics Center, Workflow Orchestration Center, Automation Engine, Intelligent
Decision Center, and Runtime Manager. Offline null adapters are used only for
tests and local construction. The Publishing Center adapter accepts an approved
publishing-plan reference; the Creator Workspace never drives a browser or
publishes directly.

## Workspace

A workspace has an ID, name, description, owner, tenant/workspace scope, status,
version, safe metadata, and timestamps. Metadata keys that commonly contain
secrets are rejected. Lifecycle states are Draft, Planning, Editing, Review,
Approved, Scheduled, Published, Archived, and Deleted.

## Projects

Projects bind campaign, publishing-plan, and workflow references with priority,
schedule, status, version, and owner. Lifecycle transitions are explicit.
Moving from Review to Approved requires an active Content Approval. Submitting a
publishing plan requires both Approved state and an active Publishing Approval.

## Calendar

Publishing, review, and reminder entries support timezone-aware daily, weekly,
and monthly views through bounded date ranges. Timezones use the IANA timezone
database and invalid names are rejected.

## Assets

Video, image, audio, subtitle, thumbnail, caption, and hashtag assets are stored
as references only. References must use `kms://` or `vault://`; plaintext paths,
credentials, cookies, and tokens are not accepted.

## Reviews and approvals

Reviews record reviewer, status, notes, timestamps, approval status, and immutable
history entries. Publishing, campaign, and content approvals record reviewer,
decision, notes, expiration, and audit events. Expired approvals cannot authorize
a transition or publishing-plan submission.

## Analytics

The dashboard reports workspace KPIs, publishing statistics delegated to the
Analytics Center, content inventory, average review and approval time, and
productivity. Prometheus metrics:

- `tiktok_creator_projects_total`
- `tiktok_creator_assets_total`
- `tiktok_creator_reviews_total`
- `tiktok_creator_approvals_total`
- `tiktok_creator_publish_plan_total`
- `tiktok_creator_latency_seconds`

## Security

Every operation enforces tenant and workspace isolation and RBAC permissions.
Approval enforcement is inside the service boundary. Asset references are
encrypted references. Audit events contain scoped identifiers and actions, not
metadata or secrets. The workspace implements no CAPTCHA bypass, restriction
circumvention, anti-detection claim, spam automation, or security bypass.

## API and dashboard

Read APIs are exposed below `/tiktok/creator-workspace` for projects, calendar,
assets, reviews, approvals, analytics, dashboard, and metrics. The production
dashboard exposes Workspace Overview, Projects, Calendar, Assets, Drafts,
Templates, Reviews, Approvals, and Analytics.

## Operations guide

Start the normal TKAI API and dashboard; no separate service is required. Check
`/tiktok/creator-workspace/metrics` and audit events during incidents. Preserve
existing approval records and encrypted references when backing up local state.
Publishing failures must be investigated in Publishing Center and Runtime Manager.

## Windows guide

Use the repository PowerShell lifecycle scripts from an ordinary user session.
Keep encrypted references in the configured local secret provider. Validate
scripts with the PowerShell parser before release. Tests use mocks and require no
TikTok account, browser session, network access, or live platform connection.
