# Cloud Execution Foundation

Cloud Execution is an offline, reference-only descriptor layer. It defines
immutable execution context, queued/running/completed/failed/cancelled/archived
states, lifecycle validation, history/result models, a thread-safe registry,
and an in-memory reference service. It never schedules Runtime work, executes a
Workflow, calls a Provider or Agent, performs Storage I/O, uses a network,
Shell, database, or cloud provider.
