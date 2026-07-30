# V9 Troubleshooting Guide

- Missing V9 routes: confirm all ten registration calls in `server.api.app`.
- Import failure: install the project and optional server dependencies in the
  active Python environment.
- Frontend build failure: use Node.js 18+ and install locked dependencies.
- Readiness failure: inspect structured diagnostics and correlated audit
  records; never print raw metadata or secret values.
- Checksum failure: discard the archive and rebuild from the recorded commit.
- Compatibility warning: review the compatibility matrix before deployment;
  advisory output never applies a migration or upgrade.
