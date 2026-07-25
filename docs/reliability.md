# Reliability Validation

RC-2 reliability validation is entirely local and bounded. It covers three
layers without making provider requests or contacting external services.

## Stress

`tests/stress` validates bounded thread and asyncio execution, EventBus
subscriber isolation, local retry decisions, composed-runtime isolation, and a
short soak smoke test. The extended soak count is opt-in:

```bash
pytest tests/stress -q
TKAI_EXTENDED_SOAK=1 pytest tests/stress/test_soak_smoke.py -q
```

## Reliability

`tests/reliability` validates lifecycle idempotency, resource cleanup,
failure-and-recovery paths, snapshot independence, bounded local history, and
object collectability. It uses standard-library `tracemalloc`, `gc`, and
`weakref` without asserting host-specific memory totals.

```bash
pytest tests/reliability -q
```

## Boundaries

These suites do not validate a real distributed backend, real network failures,
formal memory budgets, allocator behavior, or long-running production soak
durations. They are regression checks for the current in-process implementations
and their explicit lifecycle and cleanup contracts.
