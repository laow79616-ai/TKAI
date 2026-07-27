# Authentication

API keys, bearer tokens, OAuth2, OIDC, service tokens, and mutual TLS are
represented by opaque `secret://`, `vault://`, or `kms://` references.
Plaintext credentials are rejected. Credential records support revocation and
rotation timestamps without returning resolved secret values.
