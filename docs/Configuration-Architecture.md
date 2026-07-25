# Persistent Configuration

Configuration is optional and immutable. Sources merge from lowest to highest
precedence: Default, User, Workspace, Environment, then Memory. Later values
override earlier values recursively; neither source mapping is mutated.

Credential discovery remains independent: Configuration supplies only optional
provider defaults such as base URL, organization, timeout, default headers,
retry, and metadata. Runtime credentials and environment credential priority
are unchanged.

Use `tkai ai config --json` for a safe source, override-chain, application,
runtime, and provider summary. Doctor reports source, loaded-file labels, and
override chain without printing configuration secrets.
