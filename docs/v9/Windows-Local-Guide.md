# V9 Windows Local Guide

Use Python 3.10 or newer and PowerShell 7 where available. Create a virtual
environment, install the project with development dependencies, and run the
existing scripts under `scripts/`. V9 requires no new local service.

Run `python scripts/verify-v9-production.py` before packaging. PowerShell files
under `scripts/` must parse successfully; legacy non-operational templates
outside that directory are not release inputs.
