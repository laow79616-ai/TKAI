# Installer Core Foundation

**Reference Only** and **Offline Only**. The Installer consumes an explicit
resolved `ResolutionResult` and records descriptive packages in memory. It does
not download, extract artifacts, write a filesystem, call pip, invoke a
subprocess, or modify site-packages. Plans are deterministic and dependency
first: validate, prepare, install, finalize.

`ReferenceInstallationStore` is isolated and thread-safe. The Installer has no
automatic resolver invocation or registry mutation. Transactions and rollback
are intentionally not implemented until Sprint-7B.
