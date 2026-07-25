# Core Runtime

`tkai.core` provides `Context`, `Settings`, `Registry`, `Project`, `Workspace`,
and `Lifecycle`. These classes have no dependency on command-line or provider
implementations.

`Context` owns runtime services and is passed to plugins. `Registry` prevents
duplicate registrations. `Workspace` manages project directories. `Project`
serializes project metadata with timezone-aware creation timestamps.
