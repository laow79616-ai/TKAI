# Lifecycle

The lifecycle is:

`Registered -> Validated -> Loaded -> Active`

Active capabilities may be paused, disabled, or deprecated. Paused
capabilities may be reactivated or disabled. Disabled and deprecated
capabilities may be retired. Retirement is terminal. Every transition is
guarded and audited; invalid transitions fail without changing state.
