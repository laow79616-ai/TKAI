# Lifecycle

Models progress through `draft`, `training`, `ready`, `running`, `paused`,
`archived`, and `deleted`. The transition map rejects unsafe shortcuts.
Archived models are immutable from an execution perspective and deletion is a
terminal lifecycle marker suitable for downstream retention processing.
