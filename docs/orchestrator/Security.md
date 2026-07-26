# Security

RBAC grants are keyed by tenant and actor. Every plan creation and submission
requires an explicit permission. Resource lookups enforce tenant isolation.
Secret-bearing fields accept references such as `secret://vault/key`, never raw
secret material. Execution limits prevent tenant exhaustion, and privileged
actions append tenant-aware audit records.
