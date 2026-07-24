# Marketplace Server V6 Benchmark Scenarios

`benchmarks.server.reports()` emits one Markdown and one JSON report per
offline, deterministic reference scenario. The suite covers Registry
create/list/search; Publisher, Package, and Version create/search; Unified
Search; Statistics record/query/aggregate; and Health update/snapshot.

Reports are intentionally generated at execution time and are not committed as
machine-specific performance claims. They provide structural latency statistics
only and have no Ops/sec threshold.
