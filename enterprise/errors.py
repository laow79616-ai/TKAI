"""Architecture-only Enterprise error categories; no transport mapping is provided."""


class EnterpriseArchitectureError(RuntimeError):
    """Raised by future Enterprise adapters when an architecture contract is invalid."""
