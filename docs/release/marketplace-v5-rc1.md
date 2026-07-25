# Marketplace V5 RC-1 Integration Validation

Baseline: `e5e874d`. RC-1 validates explicit, offline Publisher → Publication
→ Verification/Trust → Registry → Resolver → Installer collaboration and public
imports. No Foundation receives hidden global services or performs networking,
downloads, filesystem installation, or real package execution.

Quality validation covers lifecycle, immutable snapshots, instance isolation,
and failure containment. Known benchmark gaps remain Verification coverage,
Resolver multi-scenario coverage, and Installer Reliability multi-scenario
coverage; they are recorded for RC-2 rather than implemented here.

## Integration coverage

The offline reference chain covers single-package, dependency-first and
multi-root installer inputs, plus publication rejection, trust review,
registry duplicate rejection, unresolved resolution, installer conflict,
transaction abort, and rollback consistency. It also verifies publication,
registry, installer, verification, trust, resolver, and installer snapshots
remain immutable, along with bounded eight-worker resolver reads.
