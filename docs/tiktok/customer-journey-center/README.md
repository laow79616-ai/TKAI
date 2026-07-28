# Enterprise TikTok Customer Journey Center

## Architecture

`tiktok/customer_journey` is a local, in-memory control-plane module. It models
journeys using opaque references to the existing CRM, Lead Management, Campaign,
Creator Workspace, Content Pipeline, Analytics, Performance Insights, and
Workflow centers. It does not duplicate those services or store their secrets.

## Lifecycle and stages

The lifecycle is New, Awareness, Interest, Consideration, Qualified, Opportunity,
Converted, Inactive, Archived, and Deleted. Standard visualization stages are
Awareness, Interest, Engagement, Qualification, Opportunity, Conversion,
Retention, and Reactivation. A custom stage requires a bounded 1-80 character
label. Every transition is versioned and audited.

## Touchpoints and milestones

Touchpoints contain only manual activity or opaque campaign, content, publishing,
approved-interaction, meeting, and workflow references. Milestones are Pending,
Reached, Skipped, or Manual Override; skipped and overridden milestones require a
reason and retain their timestamp in history.

## Recommendations, conversions, and analytics

Recommendations require bounded confidence and evidence references. They are
always advisory and cannot execute contact or outreach. Consent withdrawal,
expiry, or suppression blocks follow-up proposals. Conversions retain event,
opaque conversion and attribution references, timestamp, outcome, and history.
Analytics reports journey KPIs, stage duration, conversion, drop-off and
completion rates, trends, history, and the required `tiktok_customer_*` metrics.

## Security

Every operation enforces tenant and workspace isolation plus journey-specific
RBAC. References must use `ref://` or `encrypted://`. Metadata rejects secret
fields. Handoffs to CRM, Lead, Campaign, Creator Workspace, Workflow, and
Automation are reference-only and require explicit approval. No endpoint contacts
users, executes outreach, or bypasses TikTok restrictions or protections.

## Operations and Windows guide

From PowerShell in the repository:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\tiktok\test_customer_journey_center.py
.\.venv\Scripts\ruff.exe check tiktok\customer_journey tests\tiktok\test_customer_journey_center.py
.\.venv\Scripts\mypy.exe tiktok\customer_journey
Set-Location dashboard\frontend
npm run build
```

Review `/tiktok/customer-journeys/dashboard`, `/history`, `/analytics`, and
`/metrics`. Investigate isolation or approval failures through audit history.
Use mocks only; operations and tests require no live TikTok access.
