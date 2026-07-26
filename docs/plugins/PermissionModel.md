# Plugin Permission Model

Permissions are denied by default. Administrators may grant filesystem,
network, environment, secrets, API, database, workflow, and agent access.
Unknown permissions fail validation. Installation validates the complete
requested set before changing installed state. Permission changes should be
reviewed during every update.
