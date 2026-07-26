# Plugin Signing

Packages use a SHA-256 checksum for integrity and an HMAC-SHA256 signature for
authenticity in the reference implementation. Verification uses constant-time
comparison and occurs before trusted loading. Production deployments should
store signing keys in an external secret manager, rotate keys, and use an
organization-approved asymmetric signing service when distribution crosses
trust boundaries.
