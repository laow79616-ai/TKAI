# V10 Troubleshooting Guide

For import failures, confirm Python 3.10+, the repository root, and development
dependencies. For frontend failures, confirm Node.js 18+ and run the locked
dependency installation in the affected frontend. For readiness failures,
inspect structured logs, correlation IDs, health projections, configuration,
and dependency availability without logging secrets. For package failures,
rerun archive validation and compare every SHA-256 checksum.
