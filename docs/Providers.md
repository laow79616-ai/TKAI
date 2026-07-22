# Providers

Provider configuration uses `ProviderConfig(name, type, api_key, base_url,
model, timeout, max_retries, headers)`. Keep credentials in environment-backed
application configuration and never log the config object as raw data.

`ProviderManager` registers, initializes, selects, routes, and closes provider
instances. It supports a default provider and stable read-only provider names.
CLI inspection is available through `tkai ai list`, `info`, `models`, and
`doctor`; chat and embed require an application-registered provider.
