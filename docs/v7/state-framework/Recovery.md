# Recovery

`simulate_recovery` validates snapshot existence, ownership, integrity, and
version order. It returns an immutable readiness plan and records recovery
history and audit metadata. It never restores or rolls back live state.
An owning component must separately review and apply any approved recovery.
