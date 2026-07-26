# Plugin Lifecycle

The lifecycle is available → installed → enabled or disabled → uninstalled.
Loading validates versions and dependencies before construction, then invokes
`initialize()`. Unloading invokes `shutdown()` and removes the isolated dynamic
module. Updates retain immutable release history, and rollback restores the
most recent retained release. Every mutation emits an audit record.
