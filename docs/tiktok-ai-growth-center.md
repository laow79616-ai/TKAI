# Enterprise TikTok AI Growth Center

## Architecture

The local Growth Center reads opaque references through bounded ports to the
Content Pipeline, Campaign Center, Creator Workspace, Analytics Center,
Intelligent Decision Center, Continuous Optimization Center, Operations Planner,
and Control Tower. It never calls publishing or workflow-execution interfaces.

## Growth lifecycle

Profiles move through Draft, Analyzing, Proposed, Review, Approved, Tracking,
Completed, Archived, and Deleted. Transitions are versioned and audited.
Approval permits proposal creation; it does not execute work.

## Goals and KPIs

Goals cover follower growth, content output, publishing consistency, content
quality, engagement and retention trend references, account health, and bounded
custom goals. KPIs cover publishing frequency, review and pipeline throughput,
approval time, workflow and recovery success, runtime availability, resource
utilization, and trend score.

## Trends, recommendations, and forecast

Daily, weekly, monthly, quarterly, historical-comparison, and forecast-reference
records use read-only evidence. Recommendations cover opportunities, cadence,
resource and content planning, campaign planning, workflow and runtime
optimization, and risk reduction. Forecast, capacity, trend, schedule, and growth
projection simulations are offline and cannot depend on live TikTok access.

## Analytics and security

The dashboard exposes Growth Overview, Goals, KPIs, Trends, Recommendations,
Opportunities, Forecast, and Analytics. Every record carries tenant and workspace
scope. RBAC protects operations. Inputs must be opaque `ref://` or
`encrypted://` references. Secret-like metadata and audit details are rejected.
Recommendations remain advisory until human approval.

## Operations and Windows guide

Use the existing local-runtime PowerShell scripts. Check `/tiktok/growth/dashboard`,
`/tiktok/growth/analytics`, and `/tiktok/growth/metrics`. No TikTok credentials or
network access are required. Growth records reuse existing runtime infrastructure.
