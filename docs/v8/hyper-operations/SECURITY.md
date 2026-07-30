# Security

Reads require the `operations:read` permission and a compatible reader, reviewer, or administrator role. Tenant, workspace, and operations coordinates must match exactly. Recursive secret filtering redacts secret, password, token, API-key, credential, and cookie fields. Registration and aggregation produce audit records.

There is no write API, execution permission, runtime credential use, or network access.
