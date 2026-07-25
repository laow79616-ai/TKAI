# Marketplace Installer Reliability Benchmark

Reference-only, offline scenarios cover single install, dependency install,
transaction, rollback, verification, and duplicate installation. They never
download packages, modify a filesystem, invoke `pip`, or start subprocesses.
Results use the shared Markdown/JSON report format and contain no performance
gate.
