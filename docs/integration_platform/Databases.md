# Databases

SQL and NoSQL registrations refer to credentials indirectly and default to
read-only access with a maximum row/document limit. Write access and transaction
support require the explicit `integration:database:write` permission. The
platform exposes no arbitrary-query executor.
