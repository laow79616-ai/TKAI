# Encryption

At-rest and in-transit encryption are explicit host interfaces. Key records hold
KMS or HSM references, algorithms, and rotation policies rather than key bytes.
Production hosts should enforce authenticated encryption at rest and validated
TLS for all network channels.
