# Authorization

RBAC supplies permission sets through tenant-scoped role bindings. Optional ABAC
policies evaluate identity attributes and request context after RBAC succeeds.
Delegations are time bounded and cannot grant permissions the grantor lacks.
Issued token scopes are also restricted to the subject's effective permissions.
