# Publishing

Publishers are organization-scoped profiles with explicit owners, verification
state, and an optional signing-key identifier. A package can only be published
by a registered publisher. Verification is copied to each release at publish
time, and every immutable version is retained in release history.

Adapters should authenticate owners, verify organizations, scan artifacts, and
persist releases before calling the reference service. Those concerns are
intentionally not hidden inside the offline foundation.
