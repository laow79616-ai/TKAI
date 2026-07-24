# Marketplace Server V6 Release Notes

## Included foundations

- Registry, Publisher, Package, and Version descriptive local records
- Unified Search over caller-supplied entries
- Statistics over caller-supplied sources and records
- Health over caller-supplied checks and results
- Architecture Review and RC-1 integration validation
- Accelerated release validation, local benchmark scenarios, and packaging audit

## Compatibility

Marketplace Server is an independent reference product layer. It does not
change Runtime, SDK, Studio, Enterprise, Cloud, or Marketplace Foundation
public APIs. Existing Server architecture imports remain supported.

Marketplace Server has no independent distribution version and follows the
containing `tkai` package version `1.3.0`.

## Limitations

All included services are offline, pure-memory references. There is no server,
HTTP endpoint, network, database, persistence, authentication, monitoring
agent, automatic health check, package transport, or deployment facility.
