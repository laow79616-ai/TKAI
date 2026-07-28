# Fallback

Profiles define ordered fallback. Invocation uses a bounded attempt count and
classifies timeout, rate-limit, authentication, policy, invalid-request, quota,
provider, and unknown failures. Authentication, policy, and invalid-request
failures stop fallback. Provider hosts can bind their existing circuit-breaker
implementation around the provider interface.
