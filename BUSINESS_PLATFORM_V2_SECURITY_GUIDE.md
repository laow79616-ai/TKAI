# TKAI Business Platform V2 Security Guide

Administrator credentials use salted PBKDF2-SHA256 verifiers; plaintext passwords
are not retained. Tokens are opaque, expiring, and revocable. V2 routes require
authentication and every write derives its actor from the verified token. Tenant and
workspace scope is applied to every query and key. Password, token, secret, cookie,
session, and credential values are rejected or redacted from records, audit, exports,
logs, diagnostics, and manifests. There are no bypass, browser-launch, proxy-switch,
publishing, messaging, account-login, or unrestricted TikTok action endpoints.
