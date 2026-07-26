# Signing

The reference verifier validates an artifact-reference SHA-256 checksum and a
publisher-identity-bound signature using constant-time comparison. Production
adapters may replace this with KMS-backed asymmetric signatures while preserving
the verification contract and audit events.
