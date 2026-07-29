# Authorization

Call `SecurityFramework.authorize` with an `AuthorizationRequest`. The request
contains a principal, permission, tenant/workspace scope, optional capability and
service boundaries, and redacted context. Checks run in this order:

1. tenant and workspace isolation;
2. capability and service isolation;
3. inherited RBAC permission lookup;
4. active policy evaluation and priority resolution.

The immutable decision includes the reason, matched policy IDs, conflicts, and
evaluation time. Decisions do not execute TikTok actions.
