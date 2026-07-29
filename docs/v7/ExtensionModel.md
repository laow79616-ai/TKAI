# V7 Extension Model

Extensions implement `register(kernel)`. They may be loaded by a dotted
`module:attribute` path or from the `tkai.v7.extensions` entry-point group.
Discovery returns metadata only; it never activates extensions.

Operators must allow-list extensions and review their declared capabilities.
Registration should remain deterministic and side-effect free. External
connections belong in lifecycle startup and must be released during shutdown.
Extensions must use service interfaces rather than reach into another module's
state.
