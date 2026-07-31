# Deployment Handbook

Supported assets are repository Dockerfiles, Compose files, and `deployment/helm/tkai`. Pin an immutable version, verify checksums/provenance, inject secrets externally, back up state, and record rollback data. Validate prerequisites, TLS/network policy, identity, resources, probes, observability, and migrations. Promote the same artifact through staged environments after smoke tests; roll back when acceptance criteria fail.
