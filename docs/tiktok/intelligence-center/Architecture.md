# TikTok Autonomous Intelligence Center

The Intelligence Center is a tenant- and workspace-isolated, read-only
reasoning layer. It aggregates bounded snapshots from completed TikTok modules
and produces explainable reasoning, evidence-backed predictions, advisory
recommendations, history, and analytics.

## Reasoning and evidence

Profiles explicitly select allowlisted module adapters. Each adapter exposes
only `read_snapshot`; no execute, publish, update, or delete operation exists.
Reasoning records its source references, integrity references, confidence, and
assumptions. Cross-tenant adapter output is rejected.

## Predictions and recommendations

Predictions require a positive time horizon, assumptions, evidence, and
confidence in the range 0–1. Recommendations are always advisory and explicitly
require separate governance approval before any external operational handoff.
The center never executes or publishes.

## Security and operations

RBAC, tenant/workspace isolation, bounded metadata, audit events, and
secret-bearing-key rejection apply throughout. The center does not bypass
restrictions, CAPTCHA, or platform security and provides no anti-detection
guarantees.

Use the existing local Windows setup, start, health, backup, restore, and stop
PowerShell scripts. Tests use bounded doubles and require no live TikTok access.
