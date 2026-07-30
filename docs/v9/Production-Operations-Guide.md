# V9 Production Operations Guide

Before deployment, run the full validation matrix and
`python scripts/verify-v9-production.py`. Build artifacts only from a clean
worktree with `SOURCE_DATE_EPOCH` set for reproducible timestamps:

`python scripts/verify-v9-production.py --build --validate-archives`

Validate `CHECKSUMS_V9.txt` independently, retain prior configuration and
storage backups, and deploy using the existing production process. Pause,
maintenance, and kill-switch controls remain authoritative. V9 recommendations
never execute operations; operators use established runbooks for all changes.
