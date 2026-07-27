# Lifecycle

Risk profiles follow a fail-closed transition table: Draft → Active → Monitoring; monitoring can require review, pause, or resolve; paused profiles recover or resolve; resolved profiles return to monitoring or archive; archived profiles may be restored to Draft or deleted. Every transition increments the version and writes an audit event.
