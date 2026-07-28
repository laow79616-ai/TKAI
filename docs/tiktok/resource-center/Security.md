# Security

All operations enforce RBAC plus tenant and workspace isolation. Registration
rejects secrets, credential fields, executable payloads, non-JSON values, oversized
metadata, and plain external references. External references must use `vault://`,
`encrypted://`, or `reference://`. Audit details reject common secret markers.
Approval-sensitive work remains delegated to the existing module that owns it.
