# Operations Guide

1. Construct a `ServiceModel` and provider.
2. Register health checks before making the service routable.
3. Register the model and provider with a private `ServiceRegistry`.
4. Start through `ServiceLifecycle` with explicit capability grants.
5. Publish heartbeats and inspect the dashboard or GET-only API projections.
6. Pause or stop before maintenance; retire only after the service is stopped.

Use registry snapshots for diagnostics. Unknown or unavailable health removes a
service from normal routing. The default stores are process-local; embedding
applications own persistence and retention policy.
