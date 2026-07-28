# Enterprise TikTok CRM Center

## Architecture

The CRM Center is a local, single-user, tenant- and workspace-isolated aggregate for
consented business relationships. It stores organizations, minimal contacts,
relationships, opportunities, business activities, follow-up proposals, consent,
opaque document references, version history, analytics, and audit events.

Existing Lead Management, Business Workspace, Campaign, Creator Workspace,
Analytics, Performance Insights, and Workflow services are accessed only through
bounded reference or proposal ports. The CRM never executes outreach.

## Lifecycle

`New → Qualified → Active → Opportunity → Negotiation → Won/Lost → Inactive →
Archived → Deleted`. Invalid transitions are rejected and every accepted transition
creates immutable history.

## Records

- Organizations contain profile, industry, geography, tags, notes, and relationship status.
- Contacts contain business display name, role, locale, timezone, public TikTok reference,
  consent reference, and relationship. Unnecessary sensitive data is rejected.
- Relationships store only bounded lead, campaign, creator, and business-workspace references.
- Opportunities store stage, encrypted/opaque value reference, priority, probability,
  expected timeline, approval, and audit history.
- Activities are business records only: manual notes or meeting, call, email, approved
  message, task, status, and assignment references.
- Follow-ups are proposals. They require current consent and, when configured, approval
  before a reference-only workflow handoff.

## Consent and security

Consent records capture status, purpose, timestamp, withdrawal, suppression, and
audit. Withdrawal or suppression blocks handoff and suppresses existing plans.
RBAC, tenant isolation, workspace isolation, reference validation, bounded metadata,
and secret-safe audit rules are enforced in the domain service. References should be
encrypted at the persistence boundary; secrets and sensitive personal data must not
be placed in CRM fields or logs.

## Analytics and operations

The dashboard exposes overview KPIs plus organizations, contacts, relationships,
opportunities, activities, follow-ups, and history. Prometheus output includes the
six `tiktok_crm_*` metrics. Operators should review due plans, current consent,
approval state, suppression state, and audit history before any external workflow.

## API

Primary endpoints are `/tiktok/crm/organizations`, `/contacts`, `/opportunities`,
`/activities`, `/followups`, and `/analytics`; supporting endpoints expose records,
relationships, consent, history, dashboard, and metrics.

## Windows guide

From PowerShell, activate `.venv`, run `python -m pytest tests/tiktok/test_crm_center.py`,
then start the existing local runtime with `scripts\start-tkai.ps1`. Use only
loopback endpoints and the existing configured encrypted-reference providers.
