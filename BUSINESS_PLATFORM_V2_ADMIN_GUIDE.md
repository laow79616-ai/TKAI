# TKAI Business Platform V2 Administrator Guide

Set a unique bootstrap administrator through environment configuration; no default
production password exists. Assign the least-privileged role and keep tenant and
workspace headers server-controlled in deployments. Review `/business/v2/audit`,
login history, security events, health, and diagnostics regularly. Configuration APIs
must contain secret references, never secret values. Archive obsolete records and
retain backups according to policy. A restore is reference-only until an authorized
operator explicitly confirms it outside the API.
