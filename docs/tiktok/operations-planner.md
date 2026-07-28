# TikTok AI Operations Planner

## Architecture

The planner is a single-user local planning plane. It reads bounded snapshots from
existing TikTok modules and creates explainable recommendations, simulations, and
approval-gated execution handoffs. It never owns browser control or execution.

## Plan lifecycle

Plans move through Draft, Analyzing, Proposed, Pending Review, Approved, Scheduled,
Executing, Paused, Completed, Rejected, Failed, Archived, and Deleted states. The
transition table is enforced by the service, and approval is mandatory before
Approved, Scheduled, or Executing.

## Objectives, strategies, and constraints

Built-in objectives cover account health, content preparation, publishing and
collection reliability, interaction review, workflow completion, risk reduction,
resource utilization, runtime stability, and backup readiness. Custom objectives
require an explicit bounded target. Strategies are conservative by default; there
is no unrestricted autonomous mode. Numeric constraints validate minimum,
maximum, and requested values.

## Planning inputs and engine

Read-only ports obtain scoped snapshots for accounts, browsers, devices, proxies,
scheduler, resources, runtime, automation, workflows, content, publishing,
collection, interaction, risk, analytics, and local runtime. Planning validates
bounds, evaluates capacity, detects paused/unhealthy/restricted inputs, chooses
bounded concurrency and cooldowns, scores confidence, and records evidence
references. Restriction or unresolved challenge signals stop planning.

## Recommendations and simulations

Recommendations remain advisory. They include actions, schedules, resource
allocations, concurrency, cooldowns, pauses, recovery, expected outcomes, risk,
confidence, and evidence. Dry-run and what-if simulations never access TikTok.

## Approvals and execution handoff

Plan, high-risk-step, resource, and schedule approvals are scoped, expiring, and
audited. Rejections require a reason. Approved scheduled plans may hand off only
references to the Automation Engine, Workflow Center, Task Scheduler, Resource
Center, and Runtime Manager. Those systems retain execution ownership.

## Reviews, history, and analytics

Reviews capture execution, outcome, risk, resource usage, lessons, and suggested
improvements. Versioned status and audit entries provide history. Analytics expose
plan counts, success rate, planning latency, and accuracy reference fields.

## Safety and security

Tenant/workspace isolation and RBAC are enforced on every operation. Metadata and
audit details reject secret-bearing fields. Kill switches and workspace pauses
block handoff. Plans are bounded and approval-gated. The planner provides no
CAPTCHA bypass, restriction circumvention, security bypass, anti-detection
guarantee, spam automation, engagement manipulation, bulk messaging, or
unrestricted mass action.

## Operations and Windows local guide

Use Python 3.10+ from the repository virtual environment. Configure adapters with
local module services, keep all input methods read-only, and expose routes through
the existing application factory. Run `ruff check .`, `mypy`, and `pytest`; use
mock adapters in tests. Do not place cookies, sessions, proxy credentials, or
other secrets in plans, metadata, logs, or configuration.
