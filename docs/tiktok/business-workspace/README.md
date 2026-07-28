# Enterprise TikTok Business Workspace

## Architecture

The Business Workspace is TKAI V5's tenant-isolated operational control plane for
business workspaces, projects, operations, campaign references, calendars,
membership, approvals, analytics, and history. It stores only local domain state
and opaque or encrypted references. Bounded adapters coordinate with the existing
Creator Workspace, Campaign Center, Content Pipeline, Publishing Center,
Automation Engine, Execution Engine, Runtime Manager, Operations Planner,
Intelligent Decision Center, Control Tower, and Analytics Center.

It never publishes content or executes a workflow. Publishing, automation,
runtime, and execution requests are proposal-only and require a current approval.

## Workspace lifecycle

The lifecycle supports Draft, Planning, Active, Review, Approved, Running,
Paused, Completed, Archived, and Deleted. Transitions are explicit. Entering
Approved or Running requires a current approval for the resource.

## Projects

Projects organize campaign, creator workspace, content pipeline, publishing plan,
workflow, automation, and execution references with priority, schedule, status,
version, and metadata. References must use `ref://`, `kms://`, or `vault://`.

## Operations

Operations cover planning, scheduling, execution coordination, resource
coordination, approval coordination, analytics coordination, review coordination,
and recovery coordination. Coordination records receipts and audit events but does
not invoke an unrestricted action.

## Calendar

Calendar entries support daily, weekly, monthly, campaign, publishing, workflow,
review, and reminder views. Each entry carries an IANA-style timezone and an
optional non-negative reminder interval.

## Members, roles, and permissions

Membership is workspace-scoped. Built-in roles include Owner, Administrator,
Operator, Reviewer, Analyst, and Viewer. Custom roles are allowed only as bounded
sets of Workspace, Project, Campaign, Analytics, Approval, Execution Proposal,
History, and Audit permissions. Role and permission validation occurs before
assignment.

## Approvals

Workspace, project, campaign, and operational approvals record the reviewer,
decision, expiration, notes, and audit event. Expired approvals cannot authorize
coordination. Rejections require an explanation.

## Coordination

Adapters expose proposal receivers only. If an existing service has no proposal
receiver, the adapter returns an opaque coordination receipt without calling an
execution or publishing method. This preserves each module's approval, risk, and
runtime boundaries.

## Analytics and history

The dashboard provides workspace, project, campaign, operational, execution, and
resource KPIs plus trends supplied by the existing Analytics Center. Workspace,
project, approval, coordination, analytics, and audit history are tenant and
workspace isolated.

## Security

Every service operation validates tenant and workspace scope and requires RBAC.
Metadata rejects secret-bearing keys. References are encrypted or opaque. Audit
events contain identifiers and actions, never credentials. No CAPTCHA bypass,
restriction circumvention, anti-detection claim, spam automation, engagement
manipulation, bulk messaging, or unrestricted mass action is implemented.

## Operations guide

Use `/tiktok/business-workspace/dashboard` for the unified view and
`/tiktok/business-workspace/metrics` for local Prometheus text metrics. The
resource APIs live below `/tiktok/business-workspace/`. Keep approvals current
before proposing publishing or execution coordination. Review the audit trail
after lifecycle, membership, approval, and coordination changes.

## Windows guide

From PowerShell, activate `.venv`, run the local server through the existing TKAI
scripts, and open the Dashboard's **TikTok Business Workspace** page. No live
TikTok access is required for development or tests. Keep credentials in the
existing encrypted configuration systems and pass only opaque references into
this module.
