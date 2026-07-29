# Packages and Signatures

Package records contain package ID, semantic version, manifest reference,
SHA-256 checksum metadata, integrity metadata, version metadata, and source
metadata. Packages are explicitly non-installable and no remote source is
queried.

Signature records contain fingerprint, algorithm, local verification status,
and trust metadata. The framework records results supplied by trusted internal
composition; it performs no remote verification and retrieves no keys.
