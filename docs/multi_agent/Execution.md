# Execution

Plans declare parallel or sequential intent and execute in dependency order.
Each successful task creates a checkpoint. Failures honor retries and restore
the latest checkpoint; monitoring records latency and failure metrics. External
side effects must supply idempotent handlers and their own compensating
rollback operation.
