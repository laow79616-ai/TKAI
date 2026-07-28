# Rollback

A rollback plan maps completed action IDs to compensation action IDs. On failure
the platform records compensations, optionally restores the latest checkpoint,
and records the validation policy. Rollback is auditable and scope-isolated.
