# TKAI 2.0 RC-3 Packaging and Release Validation

## Release scope

RC-3 is a release-validation checkpoint for the additive, reference-only TKAI
2.0 SDK. It adds no SDK module, public API, or V1.x Runtime behavior. The SDK
is distributed as part of the current `tkai` package, whose single version
source is `1.3.0`; there is intentionally no independent SDK package version.

## Packaging and metadata

The offline setuptools build path produced a wheel and sdist for `tkai-1.3.0`.
`python -m build` was unavailable in the validation environment,
so no dependency was installed. The project build backend generated both
artifacts locally. Their audit verified the package name, version, MIT license
and license file, Python requirement, declared dependencies, and `tkai` entry
point.

Both artifacts include the `tkai` package, README, LICENSE, and default
template package data. The audit found no VCS data, virtual environments,
caches, local absolute paths, environment files, credentials, or benchmark
output in either artifact.

## Fresh-install validation

A newly created local virtual environment installed the wheel without network
access. Core package import and version inspection work with no optional
dependencies. A second clean environment with the already available declared
runtime dependencies completed CLI help, `tkai version show`, `tkai doctor`,
`tkai ai doctor --json`, SDK import smoke, default template imports, and all
three SDK reference examples. Temporary virtual environments and artifacts are
removed after validation.

## Compatibility and quality

The established package version, `tkai.__version__`, CLI version command,
README, project metadata, and release documentation all identify `1.3.0`.
RC-3 preserves V1.x APIs and the additive SDK surfaces validated by RC-1 and
RC-2. Final quality gates cover pytest, Ruff, Black, Mypy, and whitespace
validation; release tests are run three times.

## Known limitations

The SDK remains local, reference-only infrastructure. This validation does not
cover real provider networks, persistent or vector memory, remote plugins,
MCP, distributed workflow execution, Studio, or Enterprise features.

## Recommendation and manual release steps

RC-3 is ready for release approval once the final quality gate passes. This
checkpoint does not create a tag, merge a branch, publish an artifact, or start
GA. Release ownership must perform those actions separately after approval.
