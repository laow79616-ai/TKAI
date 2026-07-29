# Lifecycle

The states are Registered, Validated, Starting, Running, Paused, Stopping,
Stopped, Failed, Deprecated, and Retired. Invalid transitions fail closed.

Startup validates the dependency graph and starts providers in deterministic
dependency order. Provider failures move the affected service to Failed.
Pause, resume, stop, deprecate, and retire operations append audit events and
lifecycle history.
