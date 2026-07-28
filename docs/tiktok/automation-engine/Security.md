# Security

Tenant/workspace isolation and RBAC are enforced for every operation. Approval
is required by default. Secret-like metadata keys are rejected; integrations use
encrypted references. Audit and logs contain identities, state, and safe error
summaries only—never credentials, cookies, tokens, or session material.
