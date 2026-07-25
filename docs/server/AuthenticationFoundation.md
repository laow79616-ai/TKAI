# Marketplace Server Authentication Foundation

## Architecture

The authentication layer is a Reference Only, single-administrator framework.
`ReferenceAuthenticationService` is an explicitly injected, thread-safe
in-memory implementation. It does not access a database, environment variables,
network, or Marketplace Server Foundation storage.

## Configuration

Provide `AuthenticationConfiguration` with explicit
`AdministratorCredentials` at application composition time. The default API
dependency has no configured administrator, so login is disabled until a host
supplies credentials. Credentials must be sourced by the deploying application
and must never be logged or placed in source code.

## Token lifecycle

`POST /auth/login` verifies the configured administrator and issues an opaque
Bearer token. `GET /auth/me` validates a Bearer token through the authentication
dependency. `POST /auth/logout` revokes that token in the local service.
Tokens are in-memory, have explicit expiration, and disappear when the service
instance is discarded. They are not JWTs and are not persisted.

## Authentication flow

```
LoginRequest -> verify_credentials -> issue opaque token
Authorization: Bearer <token> -> verify_token -> AuthenticatedUser
logout -> revoke_token
```

## Known limitations

This foundation intentionally has one administrator only. It provides no RBAC,
multiple users, password hashing, password reset, OAuth, SSO, LDAP, database,
or distributed token revocation.
