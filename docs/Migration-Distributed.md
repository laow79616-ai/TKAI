# Distributed Runtime migration note

Distributed Runtime is an additive V1.2 capability. Existing V1.1 and V1.2
applications need no API, configuration, Runtime, ProviderManager, or AIClient
changes. LocalBackend is available only when an application explicitly creates
and starts a coordinator or adapter.
