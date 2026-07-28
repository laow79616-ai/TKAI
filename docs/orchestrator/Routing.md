# Routing

Each plan step declares one explicit route: `single_agent`, `multi_agent`,
`workflow`, `knowledge`, `tool`, `plugin`, or `application`. Adapters are
registered with the router by route type. Missing adapters fail closed. Step
dependencies are validated when the plan is created.
