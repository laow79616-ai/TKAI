# Pipelines

Pipelines use the fixed order Collection, Validation, Transformation, Storage,
and Analytics. This prevents an invalid configuration from storing data before
validation or transformation. Each stage obtains an external Workflow checkpoint.

A pipeline records project scope, version, latest checkpoint, and whether
recovery is enabled. Failure records a safe exception class rather than sensitive
details. Operators can retry a failed project through its lifecycle; the
Workflow integration owns checkpoint persistence and recovery execution.
