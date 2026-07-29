# RBAC

Permissions name platform capabilities. Roles contain permissions and may inherit
parent roles. Principals receive roles and may be pinned to a tenant and
workspace. Permission resolution is recursive, rejects unknown permissions and
roles, and detects inheritance cycles.

An empty or unknown role set grants nothing. Policy rules may further constrain a
granted permission by role, principal, context, scope, lifecycle, and priority.
