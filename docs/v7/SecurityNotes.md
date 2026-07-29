# TKAI V7.0 Security Notes

V7 retains deny-by-default policy, scoped RBAC, tenant, workspace, and namespace
isolation, recursive secret filtering, audit correlation, and governed runtime
eligibility. Deployment owners remain responsible for TLS, identity-provider
integration, secret-store configuration, credential rotation, and retention.

The release exposes no unrestricted public mutation endpoint, public execution
endpoint, automatic approval endpoint, runtime configuration apply endpoint,
automatic migration endpoint, secret-value retrieval endpoint, hidden-reasoning
retrieval endpoint, or chain-of-thought retrieval endpoint. Existing governed
V6 and TikTok mutation routes retain their authorization and behavior; this
release does not broaden them.

Keep `.env`, cookies, sessions, proxy credentials, private keys, runtime
databases, logs, caches, and deployment-local configuration outside release
archives. Validate `CHECKSUMS_V7.txt`, the integrity manifest, RBAC, isolation,
redaction, and audit continuity before admitting traffic.
