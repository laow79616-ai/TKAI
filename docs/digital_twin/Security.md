# Security

Every operation enforces tenant and workspace isolation plus explicit RBAC
permissions. Writes and lifecycle actions are audited. State and confidence
values are validated. Keys resembling passwords, secrets, tokens, API keys, or
authorization data are rejected from metadata, state, scenarios, evidence,
recommendations, and telemetry. API adapters must derive scope from authenticated
identity in production and must not trust arbitrary client scope headers.
