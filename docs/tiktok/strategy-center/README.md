# TikTok Autonomous Strategy Center

The Strategy Center produces bounded, explainable and reviewable operational
strategy proposals. It is advisory only: it does not execute missions, publish
content, contact users, access TikTok during scenarios, or own workflow,
planning, decision, optimization, automation, or execution infrastructure.

## Architecture

The domain package is `tiktok.strategy_center`. `models.py` defines scoped
contracts, `service.py` owns lifecycle policy and in-memory local stores,
`adapters.py` exposes read-only input and reference-only handoff ports,
`metrics.py` exports the required metrics, and `api/` registers the HTTP read
surfaces. Existing TikTok modules remain the systems of record.

## Lifecycle

`draft → analyzing → proposed → pending_review → approved → active_reference
→ completed → archived → deleted`. Rejection may occur during analysis or
review. An approved, unexpired strategy approval is mandatory before a handoff.

## Strategy types

Content, campaign, publishing, growth, operational, resource, runtime,
recovery, risk reduction, mixed, and custom bounded strategies are supported.

## Objectives

Publishing reliability, content throughput, campaign completion, workflow
success, execution success, recovery success, runtime availability, resource
efficiency, risk reduction, growth KPI, business KPI, and custom bounded
objectives are available. Targets must be finite and non-negative.

## Planning horizons

Immediate, daily, weekly, monthly, quarterly, and custom bounded windows are
supported. Custom windows require a start and a later end.

## Strategy inputs

Business intelligence, performance insights, growth, campaigns, creator
workspace, content pipeline, control tower, decisions, optimization, operations
planning, autonomous operations, missions, recovery, risk, runtime, resources,
and scheduling are consumed through read-only adapters.

## Contexts and evidence

Analysis captures scoped snapshots for the current business, campaign, content,
platform health, runtime, resource, queue, risk, recovery, and mission state.
Historical scores and protected evidence references are retained without
cookies, sessions, proxy credentials, or other secrets.

## Constraints

Approval, risk, runtime, resource, browser, device, proxy, queue, workflow,
publishing, collection, interaction, execution-window, and workspace limits use
finite, ordered bounds. Requested values outside the bounds are rejected.

## Options and evaluation

Conservative, balanced, reliability-focused, performance-focused,
growth-focused, resource-efficient, recovery-focused, risk-reduction, and
manual-assisted options are available. There is no unrestricted autonomous
default. Evaluation records objective, compliance, risk, capacity, resources,
feasibility, historical comparison, confidence, and evidence.

## Scenarios

Dry run, what-if, capacity, schedule, failure, recovery, risk, growth, and
strategy-comparison scenarios operate on snapshots and test doubles. Live
TikTok access is rejected.

## Recommendations

The selected option yields advisory objectives, schedule, resource allocation,
mission types, constraints, recovery plan, expected outcome, risk, confidence,
and evidence. A recommendation is never executable.

## Approvals and handoffs

Strategy, high-risk, resource, and runtime approvals record reviewer, notes,
expiration, rejection reason, and audit history. Approved recommendations may
be handed to the Operations Planner, Decision Center, Optimization Center,
Autonomous Operation Center, Mission Engine, Campaign Center, Creator
Workspace, Content Pipeline, or Workflow Center. Every handoff contains
references only and creates no plan, mission, workflow, or action.

## Reviews, history, and analytics

Strategy, outcome, risk, resource, mission, lessons-learned, and improvement
reviews are retained. Versioned context, constraints, options, evaluations,
scenarios, recommendations, approvals, handoffs, reviews, and audit events are
represented by scoped stores and history entries. Analytics reports totals,
states, scenario count, analysis and approval time, confidence, type
distribution, expected-benefit reference, and observed-outcome reference.

## Safety

Restrictions, unresolved challenges, kill switches, workspace pauses, and
account pauses stop analysis. Kill switches and workspace pauses stop handoffs.
Direct execution, direct publishing, direct outreach, CAPTCHA bypass,
restriction or security circumvention, anti-detection claims, spam, engagement
manipulation, bulk messaging, and unrestricted mass actions are forbidden.

## Security

Every operation enforces tenant and workspace scope plus explicit RBAC.
Metadata and audit detail reject secrets. Input ports must declare read-only
behavior. Handoffs require an unexpired approval and are reference-only.

## HTTP API

Read resources are available below `/tiktok/strategy-center/` for strategies,
objectives, contexts, constraints, options, evaluations, scenarios,
recommendations, approvals, handoffs, reviews, history, and analytics.
`dashboard` returns the operator view and `metrics` exports Prometheus text.

## Metrics

The package exports strategy total/proposed/approved/rejected counters,
scenario, recommendation, and handoff counters, plus confidence, analysis
seconds, and approval seconds.

See [OperationsGuide.md](OperationsGuide.md) and
[WindowsLocalGuide.md](WindowsLocalGuide.md).
