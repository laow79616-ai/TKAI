# Security

Every record and read is isolated by tenant and workspace. RBAC permissions
separate reading, control, operation, alert, incident, task, playbook, topology,
health, execution, and approval actions. Archive and delete transitions require
explicit approval identifiers. Metadata keys that may contain credentials are
rejected, and audit/activity metadata recursively redacts secret-bearing keys.

Production adapters must derive scope and permissions from authenticated
claims, authorize commands again at the target platform, encrypt data in
transit and at rest, and retain immutable audit records.
