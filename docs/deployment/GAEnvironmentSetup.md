# External GA Environment Setup

## Purpose

This guide prepares a reproducible host for the Marketplace Server V2 External
GA Readiness Validation. It does not replace that validation: the check must
run wheel and sdist installs, FastAPI, Dashboard, Docker Compose, PostgreSQL
migrations, and the end-to-end smoke workflow on a real host.

## Required Tools

- Python 3.12 (Python 3.10 or later is required)
- pip, `build`, and `twine`
- Node.js 22 LTS and npm
- Docker Desktop or Docker Engine with Docker Compose v2
- Internet access to the declared Python and npm package registries

The project requires no local PostgreSQL installation: the Compose topology
provides PostgreSQL for validation.

## Python Environment

Do not replace the operating system Python. Use a dedicated Python 3.12
installation and create an isolated environment in the repository root:

```text
python3.12 -m venv .venv-ga
. .venv-ga/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install build twine
python -m pip install -e ".[server,postgres,dev]"
```

Verify the required modules without printing credentials:

```text
python -m build --help
python -m twine --version
python -c "import fastapi, sqlalchemy, alembic, psycopg, server.api, server.enterprise"
```

## Node and Dashboard

Install Node.js 22 LTS. The Dashboard needs a repository lockfile before
`npm ci` can provide reproducible installation. After a lockfile is committed,
run:

```text
cd dashboard/frontend
npm ci
npm run typecheck
npm run test
npm run build
```

The Dashboard currently declares `typecheck`, `lint`, and `build`; it does not
declare an `npm test` script. Add no substitute test command during environment
preparation—record the missing script for the release decision.

## Docker and Compose

The repository supplies `docker-compose.yml` with `postgres`, `api`, and
`dashboard` services. Copy `.env.example` to `.env` and choose a local-only
development password; never commit `.env`.

```text
docker compose config
docker run --rm hello-world
docker compose build --no-cache
docker compose up -d
```

The external validation must use bounded waiting, inspect health checks, run
migrations idempotently, exercise the smoke workflow, then stop the services.

## Platform Notes

### macOS

Install Python and Node through Homebrew when it is available:

```text
brew install python@3.12 node
```

Install Docker Desktop through its official installer and start it before
running `docker info`. Docker Desktop installation is intentionally not
automated by this repository.

### Ubuntu and Debian

Install a supported Python package, Node.js LTS through an approved source,
and Docker Engine plus the Compose plugin according to your organization’s
standard package policy. Confirm `docker info` works for the current user.

### Windows

Install Python 3.12 and Node.js LTS through an approved package manager, and
install Docker Desktop with the WSL2 backend where required. Use a supported
shell to invoke the same Python and Docker commands.

## Environment Checker

Run the checker from the activated `.venv-ga`:

```text
python scripts/check_ga_environment.py
```

It only reads versions, module availability, repository prerequisite files,
and Docker daemon availability. It does not install tools, read `.env`, reveal
credentials, start containers, or modify the system. A non-zero exit status
means at least one required prerequisite is missing.

## Common Failures

- `No module named build` or `twine`: install them inside `.venv-ga`.
- `Docker daemon: not reachable`: start Docker Desktop or the Docker service,
  then verify user access with `docker info`.
- Dashboard lockfile missing: generate and review a lockfile before relying on
  `npm ci` for the external validation.
- Optional Server imports missing: install the declared `server` extra.

## Security and Next Step

Use only smoke-test-prefixed data and local placeholder credentials. Never add
passwords, bearer tokens, API-key secrets, or user-specific paths to docs,
scripts, or version control.

After every check reports PASS, re-run External GA Readiness Validation. Do
not treat this preparation step as a release decision.
