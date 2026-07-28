# Secrets

The platform accepts only provider-qualified secret references such as
`vault://production/service`. Vault and rotation providers resolve or rotate
values outside the domain. APIs and dashboard responses expose references and
versions but never resolved secret material.
