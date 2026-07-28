# Lifecycle

The lifecycle is `discovered`, `registered`, `reserved`, `allocated`, `running`,
`idle`, `paused`, `recovering`, `released`, `archived`, and `deleted`. The explicit
transition table rejects skips and terminal-state reuse. Every accepted transition
increments the version, updates the timestamp, and creates a scoped audit event.
