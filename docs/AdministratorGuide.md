# TKAI Platform Administrator Guide

## Runtime and health

Use the existing local diagnostics before configuring external services:

```bash
tkai doctor
tkai ai doctor --json
```

Doctor reports are diagnostic only. They do not validate credentials over the
network, probe providers, or modify running configuration.

## Studio administration

Studio 2.1 is an optional product layer. Its backend accepts explicit settings,
repositories, and SDK gateway dependencies. The default reference stores are
process-local memory and are appropriate for development and demonstrations,
not durable multi-user production state.

Execution records, Workflow Designer state, Execution Monitor data, and Agent
Chat reference conversations should be treated as local, non-persistent data.
The current product does not provide authentication, multi-tenancy, database
backups, WebSocket monitoring, or real-time Agent Chat transport.

## Monitoring and safety

Use the documented health, execution, and Doctor views for local inspection.
Do not place credentials in logs, snapshots, reference fixtures, or Studio
metadata. Production monitoring/exporter configuration is a host responsibility
until a separately approved platform capability is released.

## Enterprise administration boundary

Enterprise 3.0 provides offline reference descriptors and local reference
services only. It does not manage users, logins, sessions, tenant data,
authorization enforcement, audit retention, or license activation. Host
operators remain responsible for access control, data retention, and compliance
controls until separately released integrations are available.
