# Agent Runtime Observability

The runtime exposes Prometheus counters `agent_runs_total`,
`agent_success_total`, `agent_failed_total`, `agent_cancelled_total`,
`tool_calls_total`, and `tool_failures_total`, plus the
`agent_duration_seconds` summary. The existing `/metrics` endpoint appends
these metrics to current HTTP metrics; the existing observability deployment
and scrape path are unchanged.

