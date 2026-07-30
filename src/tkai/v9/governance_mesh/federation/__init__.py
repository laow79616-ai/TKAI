"""Reference-only governance federation."""

from tkai.v9.governance_mesh.governance import PolicyFabric, normalize_reference

GovernanceFederation = PolicyFabric

__all__ = ("GovernanceFederation", "PolicyFabric", "normalize_reference")
