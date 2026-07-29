# TikTok Decision Evolution Center

## Architecture

The Decision Evolution Center is a local, single-user, advisory analysis layer. It
reads bounded historical references, evaluates decision quality, and produces
explainable recommendations. It has no operational port: it cannot approve a
decision, execute a mission, publish, contact users, change runtime configuration,
or invoke a source system.

The package separates immutable domain records, the analysis service, bounded
read-only adapters, reference-only handoffs, Prometheus-compatible metrics, a
dashboard projection, and GET-only API routes. It reuses the server application,
audit conventions, security context, metrics format, and TikTok module registry.

## Lifecycle

Profiles move through Draft, Collecting, Analyzing, Ready, Review, Approved
Reference, Archived, and Deleted using explicit forward transitions. Approval
confirms only the analysis record. Every approval audit entry records
`approval_authorizes_execution=false`.

## Decision sources and integrations

The bounded source allowlist covers Intelligent Decision, Autonomous Strategy,
Operations Planner, Autonomous Operation, Mission Engine, Governance, Knowledge
Evolution, Learning, Intelligence, Optimization, Recovery, Risk Control, Business
Intelligence, Performance Insights, and Analytics centers.

Adapters expose only `read_decisions(start, end, context, limit=...)`. They return
opaque references with tenant and workspace scope. Implementations must reuse
existing source services and infrastructure; they must not copy source databases or
introduce another event, audit, security, knowledge, or reporting platform.

Knowledge Evolution, Learning, and Governance receive only
`advisory+reference://` handoff URIs. Creating a handoff does not call or mutate the
destination.

## Records, outcomes, and baselines

Decision records retain decision, context, recommendation, approval, and evidence
references plus confidence, risk, status, timestamp, and version. Outcomes compare
expected criteria with a referenced observation and retain deviation, latency, and
resource, risk, recovery, and evidence references. Versioned rolling baselines
capture historical quality, approval time, success, failure, recovery, confidence,
and risk.

## Patterns and causal safety

Supported patterns include successful, failed, delayed, overconfident,
underconfident, approval bottleneck, evidence gap, risk underestimation, resource
and schedule estimation error, and recovery selection. A pattern requires evidence
and support count. Causal claims are rejected; descriptions must use observational
language unless causality is established outside this component.

## Comparisons and evaluation

Comparisons cover expected versus observed, baseline, strategy, mission, risk,
recovery, resource, schedule, and confidence calibration. The numeric difference
is validated and every comparison includes an explanation.

Decision quality is a weighted mean of evidence completeness, constraint
compliance, risk calibration, confidence calibration, outcome accuracy, resource
accuracy, schedule accuracy, recovery appropriateness, and approval efficiency.
Every component includes its score, weight, and explanation, preserving a complete
and reproducible score breakdown.

## Confidence calibration

Calibration compares original confidence with a referenced observed accuracy.
The signed difference, distribution, trend, and explanation are retained.
Differences within five percentage points are classified as calibrated; larger
positive and negative differences are underconfidence and overconfidence.

## Lessons and recommendations

Lessons distinguish what worked, what failed, used and missing evidence, missed
constraints, risk, resource and schedule factors, recovery factors, and an
improvement summary. Recommendations cover process, evidence, risk, confidence,
approval workflow, resources, schedule, and recovery selection. Every
recommendation is advisory, cannot approve, and cannot execute.

## Reviews, versioning, and history

Human reviews retain review type, reviewer, findings, recommendations, status, and
an audit reference. Generic version records retain resource type and ID, effective
date, predecessor supersession, and change history. Profile, decision, outcome,
baseline, pattern, comparison, evaluation, confidence, lesson, recommendation,
review, and version events share a tenant/workspace-scoped history projection.

## Analytics and dashboard

Analytics expose profile, evaluation, outcome, pattern, recommendation, review and
decision totals; average quality and confidence calibration; approval time;
success, failure, and evidence completeness rates; and risk, resource, and schedule
trends. The dashboard exposes overview, profiles, decisions, outcomes, baselines,
patterns, comparisons, evaluations, confidence, lessons, recommendations, reviews,
versions, history, and analytics.

## API

All resource endpoints under `/tiktok/decision-evolution/` are GET-only:
profiles, decisions, outcomes, baselines, patterns, comparisons, evaluations,
confidence, lessons, recommendations, reviews, versions, history, and analytics.
The dashboard and metrics projections are also GET-only. Analysis writes occur
through the trusted in-process service with RBAC and audit, not public mutation
routes.

## Security

Every record and adapter result is checked for tenant and workspace scope. Actions
require read, analyze, or review RBAC permission (or the center admin permission).
Time ranges and result sizes are bounded. Metadata rejects passwords, secrets,
tokens, cookies, sessions, credentials, proxies, and API keys, and is size-limited.
Evidence is carried as opaque integrity references. Implementations must encrypt
references at rest and must not log secrets.

## Safety

The center is advisory only. It performs no automatic approval, execution,
publishing, outreach, runtime change, spam automation, CAPTCHA bypass, restriction
circumvention, security bypass, or anti-detection guarantee. Operators must respect
TikTok restrictions and challenges, risk and governance policy, workspace and
account pauses, and the kill switch. No analysis can override these controls.
