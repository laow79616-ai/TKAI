# Operations Guide

1. Register a tenant-scoped configured source and confirm Account Center
   validation and Proxy Center health.
2. Register a versioned dataset with an encrypted storage reference.
3. Create a project, configure filters, and validate the fixed pipeline.
4. Transition the project through Configured and Validated.
5. Queue a manual task or register a scheduled/recurring task through Automation.
6. Monitor dashboard history, analytics, audit, and Prometheus metrics.
7. On failure, inspect scoped health and Workflow checkpoint state; never log
   secrets or decrypted records.
8. Archive or restore datasets through authorized storage operations.

Health alerts should cover rising failure count, unhealthy configured sources,
stalled queued jobs, pipeline latency, retention failures, and checkpoint errors.
Back up only opaque catalog and audit data. Dataset backup and disaster recovery
belong to the encrypted storage service.
