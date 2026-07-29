# Security

The framework supports deny-by-default V7 RBAC, tenant isolation, workspace
isolation, owner/resource isolation, recursive secret filtering, structured
audit records, and safe tracing attributes.

Callers should provide a principal and scope references for protected lifecycle
operations. Metadata keys indicating tokens, passwords, credentials, secrets,
or API keys are redacted before storage or observation. Do not place secret
values in resource IDs, tags, or references.
