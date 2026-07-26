# Workflow Studio

Visual workflows support agent, tool, conditional, retry, and checkpoint nodes.
Graphs are validated before save. Execution is delegated through an injected
adapter to the preserved Workflow and Agent Runtime layers so checkpoint,
retry, telemetry, and plugin behavior remain consistent across Studio and SDK
clients.
