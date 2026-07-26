# Recovery

Successful steps create tenant-scoped snapshots. Resume restores a checkpoint
and continues at the next step. Rollback invokes registered compensations in
reverse order and clears materialized results. Exhausted retries enter the dead
letter queue and increment failure metrics.
