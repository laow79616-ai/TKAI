# TKAI Enterprise Tenant Boundary Foundation

## Architecture

Tenant Foundation is an explicit, offline Enterprise boundary. It is separate
from Runtime, SDK, Studio, and Studio REST. No tenant is inferred from HTTP
headers, JWTs, environment variables, ContextVars, or global state.

## Tenant Model and Context

`enterprise.tenant.Tenant` is immutable and JSON-safe. It records an explicit
id, name, slug, organization id, lifecycle status, optional edition/region,
safe metadata, and UTC timestamps. The older `enterprise.models.Tenant`
remains unchanged for compatibility.

`TenantContext` is explicit. `require_tenant` rejects an absent tenant,
`optional_tenant` preserves it, and `system_tenant_context` builds an explicit
system scope without resolving an identity.

## Resolver, Registry, and Factory

`TenantResolver` has `resolve`, `validate`, and `capabilities`. Its injected,
deterministic `ReferenceTenantResolver` uses no HTTP, JWT, database, or
network. `TenantRegistry` is thread-safe and in-memory. `TenantFactory`
requires a supplied id or injected id factory and creates no global registry.

## Organization and Membership Boundary

`OrganizationTenantBinding` declares ownership. `TenantMembershipDescriptor`
and `TenantAccessDescriptor` describe scope only: organization membership does
not grant tenant access, and Identity does not grant permission automatically.

## Isolation, Routing, and Quotas

Isolation modes are shared, logical, schema, database, cluster, and external
descriptors. They are not actual security isolation. Routes describe region,
shard, cluster, namespace, and backend only. The reference policy reads an
injected mapping; it does not access Redis, alter Runtime Scheduler, migrate
data, or fail over.

Quota descriptors can describe requests, executions, workflows, agents,
providers, storage, memory records, users, teams, or any named resource. The
reference service calculates a result only; it does not bill, persist usage,
rate-limit, or block a request.

## Lifecycle and Policies

The reference lifecycle permits explicit in-memory status transitions and never
creates resources or deletes data. Tenant policies return validation results
only; they do not authorize, route, or enforce access.

## Current Limitations

- No real tenant isolation, database partitioning, persistence, billing, or
  limiting.
- No tenant authentication or authorization enforcement.
- No audit, licensing, cloud, Kubernetes, automatic routing, migration, or
  failover.
- All reference components are offline, deterministic, caller-injected, and
  only for tests or examples.

## Next Implementation Decisions

Future work must define repository ports, ownership, consistency guarantees,
and explicit opt-in integration before persistence or enforcement is added.
