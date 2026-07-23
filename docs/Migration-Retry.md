# Retry Framework migration note

V1.1 applications require no source or configuration changes.  Existing
`tkai.ai.retry` provider-local behavior remains unchanged.  V1.2 adds an
optional `tkai.retry` package; adopt it only by explicitly creating a manager
and supplying it to application-owned execution or Policy Engine code.
