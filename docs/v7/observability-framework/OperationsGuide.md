# Operations Guide

Use the GET endpoints under `/v7/observability/` with required `tenant` and
`workspace` query parameters. Available projections are metrics, logging,
tracing, diagnostics, health, alerts, telemetry, and audit.

Run diagnostics only with side-effect-free collectors. Treat framework output
as operational metadata, not a source of business truth. Retention and alert
recommendations are declarative; operators retain control of follow-up action.
