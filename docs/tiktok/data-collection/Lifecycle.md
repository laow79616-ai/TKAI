# Lifecycle

Projects move through controlled transitions:

`Draft → Configured → Validated → Queued → Running → Completed`

Queued or running projects may be paused. Running projects may fail; failed
projects may be queued again. Completed, failed, paused, configured, or draft
projects can enter Archive through the allowed transition map. Archived projects
can be restored to Draft or marked Deleted. Deleted is terminal.

Each transition increments the project version, updates its timestamp, and emits
an operator audit record. Jobs have Queued, Running, Paused, Completed, Failed,
and Cancelled states. Cancellation is explicit and unavailable after a terminal
state. Recovery starts from the pipeline checkpoint and is mediated by Workflow.
