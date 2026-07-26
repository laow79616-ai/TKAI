# Enterprise Platform

Sprint-6 adds `tkai.enterprise`, a local reference product layer that composes
the repository's existing Enterprise and Server foundations without replacing
their public APIs.

## Tenant and isolation

Organizations own tenants; tenants own workspaces and users. Every tenant has a
namespace and quota. Role assignments and filtered queries reject cross-tenant
access. Persistence remains adapter-owned.

## RBAC and security

Permissions describe actions and resources. Roles aggregate permissions,
support bounded parent inheritance, scopes, and tenant-specific assignments.
The reference evaluator denies missing grants. Secrets are never stored in
audit metadata.

## SSO

OIDC, OAuth2, LDAP, and Active Directory are represented by explicit provider
configuration. Network discovery, redirects, token exchange, directory binds,
and secret storage belong to deployment adapters and are not performed by the
reference service.

## License and billing

Licenses model keys, activation, expiration, editions, and seats. Billing
models plans, subscriptions, quota, and usage. Invoice creation is an adapter
interface/future integration; TKAI does not fabricate payments or invoices.

## Audit

The append-only local audit stream supports login, logout, role, permission,
tenant, plugin, agent, workflow, and API events with deterministic sequence
numbers.

## API, dashboard, and observability

The transport-neutral API exposes organizations, tenants, users, roles,
permissions, license, billing, audit, and metrics under `/enterprise`.
Dashboard contracts cover all Enterprise views. Metrics are exact in-process
gauges/counters: `tenant_total`, `organization_total`, `user_total`,
`license_total`, and `audit_total`.
