# Agent Runtime Failure Handling

Validation and illegal lifecycle transitions fail without partial mutation.
Failed and cancelled runs are terminal and counted separately. Tool retry and
timeout values are policy contracts; execution remains owned by the workflow
layer. Coordination limits reject excessive fan-out or depth before any
delegated task runs, and cancellation is checked between delegations.

