# TKAI Platform Installation

## Runtime and SDK

Install the published package in a supported Python 3.10+ environment:

```bash
python -m pip install tkai
```

The Runtime and SDK ship in the same `tkai` distribution. SDK use is explicit:
applications inject adapters and local/reference services rather than creating
providers or reading credentials automatically.

For development, install the repository's development extras:

```bash
python -m pip install -e '.[dev]'
```

Verify the installed package without provider configuration:

```bash
tkai version show
tkai doctor
tkai ai doctor --json
```

## Studio

The Python Studio backend is included with the distribution. A host that starts
the optional FastAPI application must install its host dependencies explicitly;
they are intentionally not Runtime dependencies. Studio requires callers to
inject its SDK Gateway and does not create Providers, credentials, network
connections, or background workers by default.

The Studio React/Vite source is packaged for host builds. In a Node-enabled
frontend environment, install the declared frontend dependencies and run the
project's configured typecheck, lint, and build commands. No frontend build
output is distributed by Platform 1.0.

## Enterprise reference foundations

Enterprise 3.0 reference contracts ship in the same `tkai` distribution and
need no additional dependency or configuration for offline import. They are
explicitly constructed by the host; installation does not enable
authentication, persistence, authorization enforcement, audit export, or
license enforcement. See [Enterprise](Enterprise.md).

## Optional integrations

Redis support is optional and remains explicit:

```bash
python -m pip install 'tkai[redis]'
```

Do not install optional dependencies solely for local/reference workflows.
