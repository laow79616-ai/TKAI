# TKAI V7.0 Known Issues

- Optional Redis, PostgreSQL, external telemetry, AI provider, and live TikTok
  integrations require deployment-owned services and credentials and are not
  exercised by the offline release suite.
- Release builds require installed Node dependencies for Dashboard and AI Studio.
- V7 projections are intentionally read-only; execution and runtime mutation
  remain on existing governed V6/TikTok paths.

## Repository-wide mypy artifact duplication

Repository-wide mypy discovery can stop on duplicate modules copied into
generated `artifacts/` release directories. The canonical source tree is not
duplicated. Generated artifacts must remain excluded from source control and
from Python and mypy import roots.

Any duplicate-module result outside `artifacts/` is a release blocker.

## Optional production dependencies

Production database and publication workflows require their documented
optional dependencies and external services. Operators must install and
validate these prerequisites for the selected deployment profile before
admitting traffic.

There are no other known source-code release blockers at finalization time.
