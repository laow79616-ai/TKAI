# TKAI Enterprise V3.0 Architecture

## Scope

TKAI Enterprise is an additive reference product layer above TKAI Platform
1.0. This release establishes immutable domain descriptors and service
contracts in the top-level `enterprise` package, which is included in the
`tkai` distribution. It does not change the Runtime, SDK, Studio, Studio REST
API, or any existing public API.

No database, login flow, JWT validation, cloud service, marketplace, network
client, or deployment automation is implemented in this phase. The package is
deliberately reference-only and exposes no automatic integration with the
existing `tkai` public package surface.

## Architecture

```text
Enterprise control-plane contracts (future, explicit adapters)
                 |
                 v
Studio 2.1 product layer  ->  SDK 2.0 developer layer  ->  Runtime 1.3
                 |
                 v
Local infrastructure and optional adapters
```

Enterprise contracts remain separate from the existing layers. Future
integrations must use explicit adapters and dependency injection; no Enterprise
service automatically takes over Runtime, SDK, Studio, or REST behavior.

## Organization

The organization model describes the following ownership hierarchy:

- **Organization / Company** is the root business boundary.
- **Department** belongs to one organization.
- **Workspace** belongs to one department.
- **Team** belongs to one workspace and references users.
- **User**, **Role**, and **Permission** are identity and RBAC descriptors.

All current objects are frozen data models. `OrganizationDirectory` is a
future directory contract; it has no storage implementation in this release.

## Multi-tenant

`Tenant` declares an organization-associated isolation boundary and a tuple of
`Quota` descriptors. Quotas are descriptive only: no quota enforcement,
request limiter, database isolation, or tenant provisioning occurs here.

`TenantDirectory` is the future lookup boundary. Callers must explicitly pass
tenant context to future adapters rather than relying on hidden global state.

The Tenant Boundary Foundation is architecture-level and reference-only. See
[Tenant Foundation](Tenant.md). It does not add actual tenant isolation,
database partitioning, authentication, authorization enforcement, billing,
quota limiting, automatic routing, or data migration.

## Authentication

The architecture recognizes OIDC, OAuth2, SAML, LDAP, and JWT as
`IdentityProtocol` values. `IdentityProvider` defines only the future adapter
boundary for resolving a subject.

No login, session, token parsing, token validation, JWT issuance, LDAP query,
or identity-provider network call exists in this Sprint.

## Authorization

Role-based access control is represented by immutable `Role` and `Permission`
descriptors. `AuthorizationService` defines `permissions_for` and `allows` as
future decision contracts.

Attribute-based access control is intentionally reserved as an extension point;
there is no ABAC evaluator, implicit policy engine connection, or enforcement
in this architecture phase.

The Authorization Foundation now provides explicit descriptors, policy
contracts, and reference-only evaluators. See [Authorization Foundation](Authorization.md).
It does not install Runtime hooks, SDK hooks, Studio middleware, or enforcement.

## Audit

`AuditEvent` and `AuditLogService` establish an append/query contract for a
future compliance audit implementation. Events are immutable descriptors with
an explicit UTC timestamp and optional metadata.

There is no audit database, retention worker, compliance export, or history
storage in this Sprint.

The Audit Foundation now provides reference-only event, query, redaction,
retention, and integrity descriptors. See [Audit Foundation](Audit.md). It has
no persistence, SIEM/exporter, tamper-proof storage, signature, key management,
or automatic audit interception.

## License

`LicenseEdition` documents Community, Professional, and Enterprise editions.
`LicenseDescriptor` can declare organization-scoped features. It does not
validate entitlements, restrict functionality, contact a license server, or
change current Platform behavior.

The License Foundation provides offline entitlement descriptors and a
reference-only service. See [License Foundation](License.md). It does not
activate, validate signatures, read license files, or enforce features.

## Deployment

`DeploymentProfile` declares supported target topology names:

- single node
- cluster
- high availability
- Kubernetes

The profile is not a deployment controller. It creates no cluster, Kubernetes
resources, background worker, service discovery, or cloud integration.

## Service Contracts

| Contract | Future responsibility | Current behavior |
| --- | --- | --- |
| `OrganizationDirectory` | Organization, user, and role lookup | Protocol only |
| `TenantDirectory` | Tenant and quota lookup | Protocol only |
| `IdentityProvider` | Federated identity subject resolution | Protocol only |
| `AuthorizationService` | RBAC/ABAC-compatible authorization decision | Protocol only |
| `AuditLogService` | Audit append and query | Protocol only |
| `LicenseService` | Edition and entitlement lookup | Protocol only |

## Roadmap

The next Enterprise design sprint should review adapter boundaries and
integration ownership before any persistence, authentication, or authorization
implementation begins. Implementation work must preserve the explicit,
opt-in integration model and retain compatibility with Platform 1.0.

## Current Limitations

- No database or persistence layer.
- No login, OIDC/OAuth2/SAML/LDAP integration, or JWT implementation.
- No RBAC/ABAC policy evaluation or enforcement.
- No quota accounting or tenant-isolation runtime integration.
- No audit storage, compliance export, or retention processing.
- No license validation or feature enforcement.
- No cloud, marketplace, Kubernetes controller, or deployment automation.
