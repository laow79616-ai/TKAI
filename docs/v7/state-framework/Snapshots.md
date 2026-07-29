# Snapshots

Snapshots are immutable, versioned records containing state metadata and a
payload reference, never an embedded payload. References must use a URI-like
scheme. A deterministic SHA-256 integrity hash covers the snapshot fields.
`verify()` detects corruption. Snapshot history is retained in unified history.
