# Release Process

1. Cut `release/<version>` from `develop` and freeze feature scope.
2. Align versions, changelog, notes, migrations, and LTS classification.
3. Pass local validation and protected CI; failed or skipped gates are blockers.
4. Build once from the approved commit and verify metadata, contents, checksums, secrets, archives, dependencies, packages, and OpenAPI compatibility.
5. Merge to `main`, create signed `vX.Y.Z`, and merge back to `develop`.
6. Publish only with explicit authority. Released tags and artifacts are immutable.

Rollback stops distribution and issues a new patch from the last verified state.
