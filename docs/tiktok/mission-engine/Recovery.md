# Recovery

Recovery rechecks every integrated service before acting. An unresolved TikTok
restriction or challenge stops recovery. If a checkpoint exists, existing
services receive a resume reference; otherwise runtime recovery is requested.
Attempts are bounded by the mission retry limit. Operators may request rollback,
which delegates rollback to existing services and marks the mission rolled back.
