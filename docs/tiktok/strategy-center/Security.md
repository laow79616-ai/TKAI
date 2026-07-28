# Security

Tenant and workspace isolation and `tiktok:strategy-center:*` RBAC permissions
apply to every operation. Inputs are read-only; handoffs require unexpired
approval and carry references only. Metadata and logs reject passwords,
secrets, tokens, cookies, sessions, and proxy credentials.
