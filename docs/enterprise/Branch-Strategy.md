# Branch Strategy

- `main`: protected, releasable history.
- `develop`: protected integration for the next release.
- `feature/*`: short-lived work based on `develop`.
- `release/*`: stabilization; merge to `main` and back to `develop`.
- `support/*`: security and critical maintenance for a supported line.

Protected branches disallow force-push/deletion and require passing gates, resolved threads, qualified approval, and auditable history. Tags are signed and release authority restricted. Hosting administrators apply server-side policies.
