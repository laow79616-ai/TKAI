# Cookie management

Cookie login validates state before use and saves only authenticated encrypted bytes. Expired cookies update account status and metrics. Raw cookies must never be placed in payload responses, logs, metrics, browser references, or audit metadata. Production operators should supply a rotated KMS-backed encryption key.
