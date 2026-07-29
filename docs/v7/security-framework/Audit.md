# Audit

Policy registration and authorization evaluation append local immutable
`AuditEvent` records. Events cover policy, authorization, configuration,
integrity, and compliance categories and carry actor, action, outcome, reference,
redacted details, and UTC timestamp.

The audit and structured-log projections never contain plaintext secret values.
Retention and durable persistence remain the responsibility of existing platform
operations; this feature adds no remote audit sink.
