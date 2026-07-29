# TKAI V6.0 Known Issues

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
