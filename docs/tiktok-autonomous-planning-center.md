# TikTok Autonomous Planning Center

## Architecture and lifecycle

The center is a local, single-user, tenant- and workspace-scoped advisory layer. Frozen domain records and immutable version numbers cover profiles, approved input references, objectives, constraints, assumptions, candidate plans, steps, dependencies, estimates, schedules, risks, scenarios, simulations, evaluations, recommendations, reviews, approvals, and reference-only handoffs.

The lifecycle is Draft, Collecting Inputs, Generating Candidates, Simulating, Validating, Ready for Review, Under Review, Approved Reference, Rejected, Superseded, Archived, and Deleted. Approved Reference confirms only the planning artifact; it grants no execution authority.

## Inputs, planning, and simulation

Bounded read-only adapters obtain opaque references from the existing strategy, mission, operation, governance, intelligence, learning, knowledge, decision, predictive, planner, optimization, recovery, risk, BI, analytics, resource, scheduler, workflow, and command-center modules. Objectives should reference approved upstream records. Constraints are copied into immutable versions. Assumptions always retain evidence, confidence, expiry, validation status, owner, and the risk of being incorrect; they are never facts.

Candidate plans contain explainable steps, dependency graphs, advisory resource estimates, schedule windows, risk assessments, and approval requirements. Dependency validation detects missing references and cycles. Deterministic offline simulations cover timeline, capacity, resources, dependencies, constraints, risk, recovery, approval latency, schedule feasibility, and objective coverage. Comparisons and evaluations retain transparent evidence and score breakdowns.

## Reviews, approvals, versions, and handoffs

Planning, governance, risk, resource, schedule, recovery, security, and operational-readiness reviews are planning records. Approval decisions apply only to a specific plan version. Every change creates a new immutable record with effective date, supersession reference, reason, and auditable history. Handoffs contain references only and cannot call downstream services.

## Security and safety

RBAC, tenant/workspace isolation, bounded horizons/counts/results, safe metadata validation, secret filtering, evidence references, and audit events are enforced. The package exposes no execution API and performs no publishing, outreach, browser/account action, scheduling mutation, resource allocation, runtime mutation, CAPTCHA/challenge/restriction bypass, anti-abuse circumvention, spam automation, or unsupported causal claim. Account pauses, workspace pauses, kill switches, governance policies, risk controls, and recovery readiness remain mandatory downstream boundaries.

## API, dashboard, analytics, and operations

All `/tiktok/autonomous-planning/*` endpoints are GET-only views. The dashboard exposes every planning section and explicit safety flags. Prometheus text metrics cover profiles, plans, steps, simulations, validation failures, recommendations, reviews, approvals, quality, compliance, feasibility, and analysis time.

On Windows, activate `.venv`, run the focused tests and type checks, start the existing local server, and inspect `/openapi.json`. No external network, TikTok account, cookie, session, proxy, or browser is required. Operators create planning artifacts through local audited service calls, review them explicitly, and pass only an opaque reference into an existing downstream approval process.
