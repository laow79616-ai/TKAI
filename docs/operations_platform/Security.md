# Security

Tenant and workspace checks apply to every stored resource. RBAC permissions
are `operations:read`, `operations:write`, `operations:execute`, and
`operations:admin`. Destructive restores, upgrades, and rollbacks require an
external approval ID. Audits record actor, scope, action, outcome, time, and
non-secret metadata. Central logging redacts password, secret, token, and API
key assignments; notification destinations are redacted from API output.
