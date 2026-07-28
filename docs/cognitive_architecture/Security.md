# Security

Every operation enforces tenant and workspace isolation plus capability-based
RBAC. Mutations and governed processing write audit records. Decisions require
policy validation, reasoning and decisions retain evidence references, and
audit metadata removes fields whose names indicate secrets, tokens, or
passwords. Deployments must use managed secret stores and must not log secret
values.
