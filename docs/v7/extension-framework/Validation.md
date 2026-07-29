# Validation

Validation covers manifest contracts, dependency existence and versions,
permission allowlists, compatibility metadata, signature metadata, parent
references, and scope integrity. Contract constructors reject malformed IDs,
versions, checksums, installable packages, executable sandbox declarations,
and remote signature verification.

Validation is deterministic, local, bounded, callback-free, and safe to run
with mock manifests.
