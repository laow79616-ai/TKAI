# Multi-region migration note

Multi-region routing is additive and disabled by default. Existing AIClient,
ProviderManager, Runtime, and Adaptive Routing callers need no API or
configuration changes. It only takes effect when an application explicitly
creates and invokes a MultiRegion manager or adapter.
