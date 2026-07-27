# Twin Lifecycle

Twins progress through `Draft`, `Provisioned`, `Synchronized`, `Running`, and
`Paused`. Any active stage can be archived, and only an archived twin can be
deleted. Paused twins can resume running. Invalid transitions fail closed and
all accepted transitions create tenant-scoped audit entries.
