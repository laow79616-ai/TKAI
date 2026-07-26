# Enterprise Plugin SDK

Plugins provide a `plugin.json` manifest and a Python entry point using
`module:Class` syntax. The class may implement `initialize()` and `shutdown()`
lifecycle callbacks and declare tools that integrate with existing TKAI Agent
Runtime and Workflow APIs. Plugins must not mutate global registries at import
time. Use explicit dependencies and keep existing SDK contracts stable.
