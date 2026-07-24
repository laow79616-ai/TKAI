# Installer Reliability Foundation

The Installer Reliability Foundation is **Reference Only** and **Offline Only**.
Transactions, rollback, verification, events, statistics, and snapshots operate
only on `ReferenceInstallationStore` records. There is no network, download,
artifact extraction, filesystem installation, pip, subprocess, real environment
rollback, signature verification, code execution, or database transaction.

## Installer Reliability Benchmark

The bounded, offline benchmark uses the existing `BenchmarkRunner` and
`BenchmarkReport` to render Markdown and JSON. It covers single install,
linear install, transaction, rollback, and verification paths. It records no
machine-specific performance threshold and performs no real installation.
