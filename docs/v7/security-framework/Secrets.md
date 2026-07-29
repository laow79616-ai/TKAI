# Secrets

The framework stores only `SecretReference` metadata. References must use opaque
schemes such as `env://`, `file://`, or `vault-ref://`; plaintext values are
rejected. The contract supports provider, classification, version, and rotation
due metadata without retrieving or persisting secret material.

Structured metadata, logs, traces, policy context, and audit details use recursive
key-based redaction. Operators must keep real values in an existing approved
local secret mechanism and pass references only.
