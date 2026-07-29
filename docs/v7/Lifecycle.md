# V7 Lifecycle

Components transition from `created` to `initialized`, `started`, and `stopped`.
Initialization and startup follow registration order; shutdown uses reverse
order. A startup failure stops components that already started and marks the
failing component as failed.

Initialization receives a mapping containing the kernel and immutable runtime
context values. Components must not start threads or access external resources
during construction or registration.
