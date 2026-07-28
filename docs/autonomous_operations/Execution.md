# Execution

The execution engine validates dependency graphs, queues execution records, enforces
approval gates, resolves tasks in topological order, supports retries, timeouts and
checkpoints, and invokes rollback when an enabled rollback policy covers a failure.
