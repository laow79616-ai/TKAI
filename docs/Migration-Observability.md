# Observability migration note

Observability is an optional V1.1 addition. Existing V1 applications need no
API, CLI, or configuration changes. Applications that want diagnostics can
construct an `EventBus`, `EventDispatcher`, and any adapters, then provide them
to `AICommandService` or `DoctorService`. No events are emitted automatically
by existing provider calls in this release.
