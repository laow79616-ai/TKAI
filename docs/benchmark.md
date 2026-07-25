# Benchmarking

TKAI's benchmark infrastructure is an offline, deterministic harness for
structural measurement. It uses `time.perf_counter_ns` and a frozen
`BenchmarkResult`; it has no provider, service, or network dependency.

Use the module entry points listed in the [RC-2 benchmark
summary](release/v1.2-rc2-benchmark-summary.md). Each produces a Markdown
table by default, or JSON with `--json`.

```bash
python -m benchmarks.combined_runtime
python -m benchmarks.combined_runtime --json
```

The default workloads are intentionally small. They verify benchmark wiring and
result shape; they are not performance gates. Do not compare raw timings across
hosts or use RC-2 output as an operations-per-second target.

The benchmark result has operation-count, elapsed-time, throughput, mean,
percentile, minimum, and maximum fields. The percentile implementation is
documented in `benchmarks.statistics` and is deterministic for a fixed input.

For the release manifest without host-specific figures, see
`docs/release/v1.2-rc2-benchmark-summary.json`.
