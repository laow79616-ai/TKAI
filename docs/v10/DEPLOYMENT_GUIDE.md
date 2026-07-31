# V10 Deployment Guide

Build from the recorded source commit with Python 3.10+ and Node.js 18+.
Validate `artifacts/CHECKSUMS_V10.txt` and `INTEGRITY_MANIFEST_V10.json`, then
use the existing deployment mechanism and environment-specific configuration.
No automatic migration or upgrade occurs. Keep secrets in the established
secret provider and never in archives, command history, or environment files
committed to source.
