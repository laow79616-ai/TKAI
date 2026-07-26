# Marketplace Security

Trust is deny-by-default at adapter boundaries: authenticate publishers,
authorize owners, verify organization identity, validate integrity and
signatures, scan packages, enforce compatibility and license seats, moderate
reviews, and audit lifecycle operations. Never put signing secrets, payment
credentials, license material, or package payloads in catalog metadata.

The reference service is intentionally local and makes no claim of sandbox,
malware scanning, cryptographic key custody, payment-card compliance, or
distributed transaction safety.
