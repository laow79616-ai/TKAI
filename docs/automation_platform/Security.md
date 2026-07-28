# Security

Every resource carries tenant and workspace scope. Reads and mutations enforce
scope and RBAC (`automation:read`, `automation:write`, `automation:execute`,
`automation:approve`, or `automation:admin`). Lifecycle, approval, and execution
activity is audited. Actions and triggers accept only secret-manager references.
