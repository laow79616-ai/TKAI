# Cloud Deployment Foundation

Cloud Deployment is a reference-only declaration layer. It provides immutable
deployment descriptors, explicit context, target and strategy descriptions,
deterministic plans, lifecycle transition validation, result descriptors, and
an in-memory reference service. It never calls Kubernetes, Docker, a cloud API,
Shell, network, database, storage backend, or execution engine.

Targets may describe local, container, Kubernetes, serverless, VM, managed, or
external destinations; these kinds never open a connection. Plans validate
duplicate IDs, unknown dependencies, and simple self cycles only. The reference
service stores descriptors locally, supports explicit transitions and idempotent
close, and performs no provisioning, rollback, audit, or license operation.
