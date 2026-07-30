# TKAI 9.0.0 Release Notes

TKAI V9 is a compatibility-preserving platform release comprising exactly ten
adaptive components. All V9 APIs are authenticated, advisory, and GET-only.
The release introduces no TikTok business behavior or runtime mutation.

The supported baseline is Python 3.10 or newer. Node.js 18 or newer is needed
to build the Dashboard and AI Studio; PowerShell 7 is recommended on Windows.
No automatic migration is performed. V8 deployments may upgrade in place after
backing up configuration and storage, validating environment prerequisites, and
running `python scripts/verify-v9-production.py`.

No known release-blocking issue is present. The annotated `v9.0.0` tag marks
the final GA release commit.
