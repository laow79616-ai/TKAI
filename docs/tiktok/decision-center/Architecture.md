# TikTok AI Intelligent Decision Center Architecture

The Decision Center is an advisory layer over existing TKAI V5.0 TikTok modules.
It collects workspace-scoped snapshots through read-only adapters, evaluates
objectives, constraints, risk, capacity, and resources, and produces explainable
recommendations. It owns no browser, device, account, workflow, or execution
driver. Approved output is an encrypted execution-proposal reference only.

The package boundaries are `decisions`, `contexts`, `strategies`, `constraints`,
`evaluations`, `recommendations`, `approvals`, `evidence`, `history`, `analytics`,
`dashboard`, and `api`.
