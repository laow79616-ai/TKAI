# Retry Framework

`tkai.retry` is an optional, local retry framework.  It does not replace the
existing provider-local retry behavior in `tkai.ai.retry`, and it never
automatically wraps ProviderManager, AIClient, or ProviderRuntime calls.

## Core types

`RetryPolicy` defines a named maximum-attempt count, a `BackoffStrategy`, and an
exception classifier.  The default policy allows exactly one attempt, so it
performs no retry.  `RetryBudget` is immutable and operation-local; no retry
state is distributed or persisted.

`classify_exception()` recognizes local timeout, connection/network, and
rate-limit-shaped failures as retryable.  Other failures are permanent by
default.  Callers can inject a classifier and sleeper for deterministic tests.

## Explicit execution

Construct `RetryManager`, register a policy if named lookup is needed, then
call `manager.run(operation, policy=...)`.  `RuntimeRetryAdapter` is an
explicit helper around that call; it does not modify ProviderRuntime.

## Policy Engine and observability

`RetryPolicyAdapter` can be registered in `PolicyManager` to put the explicit
RetryManager into a `PolicyContext`.  It does not execute a retry itself.
`RetryScheduled` and `RetryExhausted` events optionally publish through the
shared EventBus.  Doctor and `tkai ai retry` only inspect policy metadata.

## Limitations

The framework is synchronous, in-process, and caller-driven.  It does not
provide distributed state, Redis, hedged requests, speculative execution,
automatic ProviderManager takeover, or a change to existing provider defaults.
