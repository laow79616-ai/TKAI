# Enterprise TikTok Lead Management Center

## Architecture and lifecycle

`tiktok/lead_center` is an in-memory, local single-user control-plane module with
tenant/workspace scope checks, RBAC, immutable source provenance, version history,
audit events, bounded adapters, Prometheus metrics, and FastAPI routes. The
lifecycle is New/Imported → Validated → Duplicate Review → Qualified or
Unqualified → Assigned → Follow-Up Planned → Engaged → Converted, with Paused,
Archived, and Deleted terminal controls.

## Sources, imports, and deduplication

Sources are explicit enum values and always retain an opaque source reference.
CSV and JSON imports require schema mapping, preview/dry-run validation, error
reports, duplicate checks, and a maximum of 1,000 rows. Spreadsheet systems may
provide a bounded exported CSV/JSON reference; the center does not ingest an
unbounded workbook. Exact public/external references and a bounded 0.85 display
name similarity produce candidates. Merges are proposals requiring manual review.

## Qualification, scoring, and segments

Qualification records business, campaign, geographic, and language relevance,
a reason, manual-review state, and evidence references. Scores use only bounded
business fit, engagement reference, recency, source quality, consent state, and
explicit risk flags. Every score explains its equal weighting and penalty.
Protected characteristics are rejected. Segments support campaign, product,
region, language, interest, status, priority, and bounded custom membership.

## Assignment, consent, activities, and follow-ups

Assignments record owner/operator/reviewer, rule reference, capacity, priority,
expiry, and history. Consent records retain source, purpose, timestamp, expiry,
withdrawal and suppression. Withdrawal activates suppression. Activities are
manual notes or opaque call/email/approved-message/meeting/campaign/interaction
references; there is no direct messaging. Follow-ups are manual task proposals.
Missing consent/lawful basis, expiry, withdrawal, or suppression blocks them.

## Handoffs and integration

Business Workspace, Campaign Center, Creator Workspace, Interaction Center,
Workflow Center, Automation Engine, Task Scheduler, and future CRM handoffs are
approval-gated opaque-reference proposals. Existing source systems are consumed
through bounded read-only ports. No outreach, workflow execution, collection, or
publishing infrastructure is duplicated.

## Analytics, privacy, safety, and security

The dashboard exposes totals, source/stage/score/consent distributions,
qualification and conversion reference rates, and timing metrics. Metadata is
size-bounded and rejects secrets and protected attributes. References are opaque
or public identifiers. Tenant/workspace isolation, RBAC, audit, data minimization,
purpose limitation, consent and suppression enforcement apply throughout.
Private scraping, unsolicited messaging, spam, engagement manipulation, CAPTCHA
bypass, restriction circumvention, security bypass, and anti-detection claims are
not implemented. Paused leads cannot hand off.

## Operations and Windows local guide

Start TKAI with `scripts\start-tkai.ps1`, then inspect
`/tiktok/leads/dashboard`, `/analytics`, `/history`, and `/metrics`. Use
`scripts\stop-tkai.ps1` to stop it. Imports should always be previewed before
commit. Resolve consent, suppression, approval, pause, kill-switch, and risk
conditions manually. Tests use bounded doubles and never require TikTok access.
